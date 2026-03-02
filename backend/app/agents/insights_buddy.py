import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.services.embedding_service import embedding_service
from app.services.openai_service import openai_service
from app.db.models.resolution import Resolution
from app.db.models.ai_audit_log import AIAuditLog
from app.schemas.ticket import TicketAnalysisRequest, AnalysisResult, ResolutionOption

class InsightsBuddyAgent:
    """AI Agent for analyzing tickets and suggesting resolutions"""
    
    def __init__(self):
        self.agent_name = "InsightsBuddy"
    
    async def analyze_ticket(self, 
                           ticket_request: TicketAnalysisRequest, 
                           db: Session) -> AnalysisResult:
        """
        Main function to analyze a ticket and provide resolution suggestions
        """
        try:
            # Generate embedding for the current ticket
            ticket_text = embedding_service.prepare_text_for_embedding(
                ticket_request.title, 
                ticket_request.description
            )
            ticket_embedding = await embedding_service.generate_embedding(ticket_text)
            
            # Find similar historical resolutions
            similar_resolutions = await self._find_similar_incidents(ticket_embedding, db)
            
            # Generate resolution suggestions using LLM
            resolution_options = await self._generate_resolution_suggestions(
                ticket_request, similar_resolutions
            )
            
            # Create audit log in a separate transaction to avoid rollback issues
            try:
                audit_log = await self._create_audit_log(
                    ticket_request, resolution_options, similar_resolutions, db
                )
            except Exception as audit_error:
                print(f"Warning: Could not create audit log: {str(audit_error)}")
                # Continue without audit log
                audit_log = None
            
            # Determine category based on ticket content
            category = self._determine_category(ticket_request)
            
            # Calculate overall confidence from resolution options
            avg_confidence = sum(opt.confidence_score for opt in resolution_options) / len(resolution_options) if resolution_options else 0.5
            
            # Determine if escalation is needed based on confidence and complexity
            escalation_needed = (
                avg_confidence < 0.6 or 
                len(similar_resolutions) == 0 or
                any("critical" in opt.title.lower() or "urgent" in opt.description.lower() for opt in resolution_options)
            )
            
            # Generate reasoning
            reasoning = f"Analyzed ticket using {'vector similarity' if similar_resolutions else 'pattern matching'}. Found {len(similar_resolutions)} similar cases."
            
            return AnalysisResult(
                ticket_id=ticket_request.ticket_id,
                category=category,
                reasoning=reasoning,
                confidence_score=avg_confidence,
                resolution_options=resolution_options,
                similar_incidents_count=len(similar_resolutions),
                escalation_recommended=escalation_needed,
                analysis_timestamp=datetime.utcnow(),
                audit_log_id=audit_log.ai_event_id if audit_log else None
            )
            
        except Exception as e:
            print(f"Error in InsightsBuddyAgent.analyze_ticket: {str(e)}")
            # Rollback the transaction if something went wrong
            db.rollback()
            raise e
    
    async def _find_similar_incidents(self, 
                                    ticket_embedding: List[float], 
                                    db: Session, 
                                    limit: int = 5) -> List[Resolution]:
        """Find similar resolutions using vector similarity"""
        try:
            # Skip vector search if no embedding provided, use text similarity instead
            if not ticket_embedding or not any(ticket_embedding):
                print("No valid embedding, using text-based similarity search")
                return await self._find_text_similar_resolutions(db, limit)
            
            # Use text() with proper parameterization for pgvector
            query = text("""
                SELECT resolution_id, resolution_text, root_cause, outcome, confidence_score,
                       embedding <=> CAST(:embedding AS vector) as distance
                FROM resolutions 
                WHERE embedding IS NOT NULL 
                  AND is_kb = true
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """)
            
            # Convert embedding to proper format for pgvector
            embedding_str = '[' + ','.join(map(str, ticket_embedding)) + ']'
            
            result = db.execute(query, {
                "embedding": embedding_str,
                "limit": limit
            })
            
            resolutions = []
            for row in result:
                resolution = Resolution()
                resolution.resolution_id = row.resolution_id
                resolution.resolution_text = row.resolution_text
                resolution.root_cause = row.root_cause
                resolution.outcome = row.outcome
                resolution.confidence_score = row.confidence_score
                # Store similarity score as a custom attribute (1 - distance)
                resolution.similarity_score = 1.0 - float(row.distance) if row.distance is not None else 0.0
                resolutions.append(resolution)
            
            return resolutions
            
        except Exception as e:
            print(f"Error finding similar resolutions: {str(e)}")
            # Fall back to text-based search
            try:
                return await self._find_text_similar_resolutions(db, limit)
            except:
                return []
    
    async def _find_text_similar_resolutions(self, db: Session, limit: int = 3) -> List[Resolution]:
        """Find resolutions using text similarity (fallback when embeddings fail)"""
        try:
            # Get all knowledge base resolutions for now
            query = text("""
                SELECT resolution_id, resolution_text, root_cause, outcome, confidence_score
                FROM resolutions 
                WHERE is_kb = true
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            result = db.execute(query, {"limit": limit})
            
            resolutions = []
            for row in result:
                resolution = Resolution()
                resolution.resolution_id = row.resolution_id
                resolution.resolution_text = row.resolution_text
                resolution.root_cause = row.root_cause
                resolution.outcome = row.outcome
                resolution.confidence_score = row.confidence_score
                # Set a default similarity score
                resolution.similarity_score = 0.7
                resolutions.append(resolution)
            
            return resolutions
            
        except Exception as e:
            print(f"Error in text-based resolution search: {str(e)}")
            return []
    
    async def _generate_resolution_suggestions(self, 
                                             ticket_request: TicketAnalysisRequest,
                                             similar_resolutions: List[Resolution]) -> List[ResolutionOption]:
        """Generate resolution suggestions using LLM analysis"""
        try:
            # Prepare context from similar resolutions
            context_text = self._prepare_resolution_context(similar_resolutions)
            
            # Create prompt for LLM
            prompt = self._create_analysis_prompt(ticket_request, context_text)
            
            # Try to get LLM response
            if openai_service.client:
                try:
                    messages = [
                        {"role": "system", "content": "You are InsightsBuddy, an expert IT support analyst. Analyze the ticket and provide structured resolution suggestions."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    response_text = await openai_service.generate_completion(messages, temperature=0.3)
                    
                    # Parse the response into structured format
                    resolution_options = self._parse_resolution_response(response_text)
                    
                    if resolution_options:
                        return resolution_options
                except Exception as llm_error:
                    print(f"LLM failed: {llm_error}")
            
            # Fallback: Generate intelligent suggestions based on ticket patterns
            return self._generate_pattern_based_suggestions(ticket_request)
            
        except Exception as e:
            print(f"Error generating resolution suggestions: {str(e)}")
            return self._generate_pattern_based_suggestions(ticket_request)
    
    def _prepare_resolution_context(self, similar_resolutions: List[Resolution]) -> str:
        """Prepare context text from similar resolutions"""
        if not similar_resolutions:
            return "No similar historical resolutions found."
        
        context_parts = ["Similar Historical Resolutions:"]
        
        for i, resolution in enumerate(similar_resolutions, 1):
            similarity = getattr(resolution, 'similarity_score', 0.0)
            context_parts.append(f"""
Resolution {i} (Similarity: {similarity:.2f}, Confidence: {resolution.confidence_score or 'N/A'}):
Resolution: {resolution.resolution_text}
Root Cause: {resolution.root_cause or 'Not specified'}
Outcome: {resolution.outcome or 'Not specified'}
""")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, 
                              ticket_request: TicketAnalysisRequest, 
                              context_text: str) -> str:
        """Create the analysis prompt for the LLM"""
        return f"""
Analyze this support ticket and provide resolution suggestions based on similar historical resolutions.

CURRENT TICKET:
Title: {ticket_request.title}
Description: {ticket_request.description}

{context_text}

Please provide 3-5 resolution options in the following JSON format:
{{
    "resolution_options": [
        {{
            "title": "Clear, actionable title",
            "description": "Detailed step-by-step resolution",
            "confidence_score": 0.85,
            "reasoning": "Why this solution is recommended",
            "estimated_time": "15 minutes",
            "risk_level": "low|medium|high"
        }}
    ]
}}

Base your suggestions on the historical resolutions and provide realistic confidence scores based on similarity and success rates.
"""
    
    def _parse_resolution_response(self, response_text: str) -> List[ResolutionOption]:
        """Parse LLM response into ResolutionOption objects"""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            response_data = json.loads(json_text)
            
            resolution_options = []
            for option_data in response_data.get("resolution_options", []):
                option = ResolutionOption(
                    title=option_data.get("title", "Unknown Resolution"),
                    description=option_data.get("description", "No description provided"),
                    confidence_score=option_data.get("confidence_score", 0.5),
                    reasoning=option_data.get("reasoning", "No reasoning provided"),
                    estimated_time=option_data.get("estimated_time", "Unknown"),
                    risk_level=option_data.get("risk_level", "medium")
                )
                resolution_options.append(option)
            
            return resolution_options
            
        except Exception as e:
            print(f"Error parsing resolution response: {str(e)}")
            # Return a fallback resolution
            return [ResolutionOption(
                title="Manual Investigation Required",
                description="Unable to automatically generate resolution. Manual investigation by support team required.",
                confidence_score=0.3,
                reasoning="Automatic analysis failed - human intervention needed",
                estimated_time="30-60 minutes",
                risk_level="low"
            )]
    
    def _generate_pattern_based_suggestions(self, ticket_request: TicketAnalysisRequest) -> List[ResolutionOption]:
        """Generate intelligent suggestions based on ticket content patterns"""
        title_lower = ticket_request.title.lower()
        desc_lower = ticket_request.description.lower()
        
        # Pattern matching for common issues
        if any(word in title_lower or word in desc_lower for word in ['outlook', 'email', 'sync', 'mailbox']):
            return self._get_email_resolution_patterns()
        elif any(word in title_lower or word in desc_lower for word in ['access', 'permission', 'denied', 'login']):
            return self._get_access_resolution_patterns()
        elif any(word in title_lower or word in desc_lower for word in ['server', 'down', 'timeout', 'connection']):
            return self._get_server_resolution_patterns()
        elif any(word in title_lower or word in desc_lower for word in ['dashboard', 'blank', 'loading', 'ui']):
            return self._get_ui_resolution_patterns()
        else:
            return self._get_generic_resolution_patterns()
    
    def _get_email_resolution_patterns(self) -> List[ResolutionOption]:
        return [
            ResolutionOption(
                title="Check Outlook Profile and Connectivity",
                description="1. Verify internet connection\n2. Test Outlook in Safe Mode (outlook.exe /safe)\n3. Check if OWA (Outlook Web App) works\n4. Recreate Outlook profile if needed",
                confidence_score=0.8,
                reasoning="Email sync issues are commonly resolved by profile recreation and connectivity checks",
                estimated_time="15-30 minutes",
                risk_level="low"
            ),
            ResolutionOption(
                title="Exchange Server Configuration Check",
                description="1. Verify Exchange server settings\n2. Check autodiscover configuration\n3. Validate SSL certificates\n4. Test with different email client",
                confidence_score=0.7,
                reasoning="Server-side configuration issues often cause sync problems",
                estimated_time="20-45 minutes",
                risk_level="medium"
            )
        ]
    
    def _get_access_resolution_patterns(self) -> List[ResolutionOption]:
        return [
            ResolutionOption(
                title="Permission and Access Rights Verification",
                description="1. Check user permissions in admin panel\n2. Verify group memberships\n3. Test with different user account\n4. Clear browser cache and retry",
                confidence_score=0.85,
                reasoning="Access denied errors are typically permission-related",
                estimated_time="10-20 minutes",
                risk_level="low"
            ),
            ResolutionOption(
                title="Account and Authentication Review",
                description="1. Verify account is active and not locked\n2. Check MFA/2FA settings\n3. Reset password if necessary\n4. Review recent permission changes",
                confidence_score=0.75,
                reasoning="Authentication issues often require account verification",
                estimated_time="15-25 minutes",
                risk_level="low"
            )
        ]
    
    def _get_server_resolution_patterns(self) -> List[ResolutionOption]:
        return [
            ResolutionOption(
                title="Server Connectivity and Health Check",
                description="1. Ping server to test basic connectivity\n2. Check server status in monitoring tools\n3. Verify firewall and network settings\n4. Restart server services if needed",
                confidence_score=0.9,
                reasoning="Server connectivity issues require systematic network and service verification",
                estimated_time="20-40 minutes",
                risk_level="medium"
            ),
            ResolutionOption(
                title="Service and Application Restart",
                description="1. Restart the affected service/application\n2. Check system logs for errors\n3. Verify disk space and resources\n4. Test with minimal configuration",
                confidence_score=0.8,
                reasoning="Many server issues are resolved by service restarts",
                estimated_time="10-15 minutes",
                risk_level="low"
            )
        ]
    
    def _get_ui_resolution_patterns(self) -> List[ResolutionOption]:
        return [
            ResolutionOption(
                title="Browser and Cache Troubleshooting",
                description="1. Clear browser cache and cookies\n2. Try in incognito/private mode\n3. Test with different browser\n4. Disable browser extensions",
                confidence_score=0.85,
                reasoning="UI loading issues are often browser or cache related",
                estimated_time="10-15 minutes",
                risk_level="low"
            ),
            ResolutionOption(
                title="Application Data and Settings Reset",
                description="1. Clear application data/preferences\n2. Reset to default settings\n3. Check for JavaScript errors in browser console\n4. Verify user permissions for UI features",
                confidence_score=0.7,
                reasoning="Dashboard issues may require application reset",
                estimated_time="15-25 minutes",
                risk_level="medium"
            )
        ]
    
    def _get_generic_resolution_patterns(self) -> List[ResolutionOption]:
        return [
            ResolutionOption(
                title="Initial Troubleshooting Steps",
                description="1. Gather detailed error messages and screenshots\n2. Check system logs for related entries\n3. Verify recent changes or updates\n4. Test with minimal configuration",
                confidence_score=0.6,
                reasoning="Standard troubleshooting approach for unrecognized issues",
                estimated_time="20-30 minutes",
                risk_level="low"
            ),
            ResolutionOption(
                title="Escalation and Expert Review",
                description="1. Document all symptoms and attempted solutions\n2. Escalate to technical specialist\n3. Schedule detailed investigation session\n4. Consider vendor support if applicable",
                confidence_score=0.4,
                reasoning="Complex or unknown issues require expert intervention",
                estimated_time="45-90 minutes",
                risk_level="low"
            )
        ]
    
    async def _create_audit_log(self, 
                              ticket_request: TicketAnalysisRequest,
                              resolution_options: List[ResolutionOption],
                              similar_resolutions: List[Resolution],
                              db: Session) -> AIAuditLog:
        """Create audit log entry for this analysis"""
        try:
            input_json = {
                "ticket_id": str(ticket_request.ticket_id),
                "title": ticket_request.title,
                "description": ticket_request.description
            }
            
            output_json = {
                "resolution_options": [
                    {
                        "title": option.title,
                        "description": option.description,
                        "confidence_score": option.confidence_score,
                        "reasoning": option.reasoning,
                        "estimated_time": option.estimated_time,
                        "risk_level": option.risk_level
                    } for option in resolution_options
                ]
            }
            
            confidence_json = {
                "avg_confidence": sum(o.confidence_score for o in resolution_options) / len(resolution_options) if resolution_options else 0,
                "similar_resolutions_count": len(similar_resolutions)
            }
            
            supporting_incident_ids = [resolution.resolution_id for resolution in similar_resolutions]
            
            audit_log = AIAuditLog(
                ticket_id=ticket_request.ticket_id,
                agent_name=self.agent_name,
                model_name=openai_service.model,
                input_json=input_json,
                output_json=output_json,
                confidence_json=confidence_json,
                supporting_incident_ids=supporting_incident_ids,
                was_used=False  # Will be updated when user selects a resolution
            )
            
            # Use a fresh transaction for audit log to avoid rollback issues
            try:
                db.add(audit_log)
                db.commit()
                db.refresh(audit_log)
            except Exception as commit_error:
                db.rollback()
                raise commit_error
            
            return audit_log
            
        except Exception as e:
            print(f"Error creating audit log: {str(e)}")
            try:
                db.rollback()
            except:
                pass
            raise e
    
    def _determine_category(self, ticket_request: TicketAnalysisRequest) -> str:
        """Determine ticket category based on content"""
        title_lower = ticket_request.title.lower()
        desc_lower = ticket_request.description.lower()
        
        if any(word in title_lower or word in desc_lower for word in ['outlook', 'email', 'sync', 'mailbox']):
            return "email_support"
        elif any(word in title_lower or word in desc_lower for word in ['access', 'permission', 'denied', 'login']):
            return "access_management"
        elif any(word in title_lower or word in desc_lower for word in ['server', 'down', 'timeout', 'connection']):
            return "infrastructure"
        elif any(word in title_lower or word in desc_lower for word in ['dashboard', 'blank', 'loading', 'ui']):
            return "ui_issues"
        else:
            return "general_support"

# Global instance
insights_buddy = InsightsBuddyAgent()
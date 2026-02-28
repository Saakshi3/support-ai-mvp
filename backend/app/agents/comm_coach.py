import json
import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.openai_service import openai_service
from app.db.models.ai_audit_log import AIAuditLog
from app.db.models.email import Email
from app.db.models.ticket import Ticket
from app.schemas.ticket import EmailDraftRequest, EmailDraft

class CommCoachAgent:
    """AI Agent for drafting professional email responses"""
    
    def __init__(self):
        self.agent_name = "CommCoach"
    
    async def draft_email(self, 
                         ticket: Ticket,
                         draft_request: EmailDraftRequest, 
                         created_by_user_id: uuid.UUID,
                         db: Session) -> EmailDraft:
        """
        Draft an email response based on ticket information
        """
        try:
            # Generate email draft using LLM or patterns
            email_content = await self._generate_email_content(ticket, draft_request)
            
            # Save draft to database
            email_record = await self._save_email_draft(
                ticket.ticket_id, email_content, created_by_user_id, db
            )
            
            # Create audit log
            audit_log = await self._create_audit_log(ticket, draft_request, email_content, db)
            
            return email_content
            
        except Exception as e:
            print(f"Error in CommCoachAgent.draft_email: {str(e)}")
            raise e
    
    async def save_email_draft(self, 
                             draft_request: EmailDraftRequest,
                             email_draft: EmailDraft,
                             created_by_user_id: uuid.UUID,
                             db: Session) -> Email:
        """Save the drafted email to the database"""
        try:
            email = Email(
                ticket_id=draft_request.ticket_id,
                type="DRAFT",
                subject=email_draft.subject,
                body=email_draft.body,
                created_by=created_by_user_id
            )
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            return email
            
        except Exception as e:
            print(f"Error saving email draft: {str(e)}")
            db.rollback()
            raise e
    
    async def _generate_email_content(self, draft_request: EmailDraftRequest) -> EmailDraft:
        """Generate email content using LLM"""
        try:
            # Create detailed prompt for email generation
            prompt = self._create_email_prompt(draft_request)
            
            messages = [
                {
                    "role": "system", 
                    "content": """You are CommCoach, a professional communication expert specializing in customer support emails. 
                    You write clear, empathetic, professional emails that build customer confidence and provide excellent support.
                    Always include: proper greeting, empathy/acknowledgment, clear action steps, and professional closing."""
                },
                {"role": "user", "content": prompt}
            ]
            
            response_text = await openai_service.generate_completion(messages, temperature=0.5)
            
            # Parse the email content
            email_draft = self._parse_email_response(response_text)
            
            return email_draft
            
        except Exception as e:
            print(f"Error generating email content: {str(e)}")
            # Return a fallback email
            return EmailDraft(
                subject="Re: Your Support Request",
                body="Thank you for contacting support. We are reviewing your request and will provide an update soon.",
                confidence_score=0.3,
                draft_reasoning="Fallback email due to generation error"
            )
    
    def _generate_pattern_based_email(self, ticket: Ticket, draft_request: EmailDraftRequest) -> EmailDraft:
        """Generate email using patterns when LLM is unavailable"""
        email_type = draft_request.email_type.upper()
        tone = draft_request.tone
        recipient_context = draft_request.recipient_context
        
        if email_type == "UPDATE":
            return self._create_update_email(ticket, tone, recipient_context)
        elif email_type == "RESOLUTION":
            return self._create_resolution_email(ticket, tone, recipient_context)
        elif email_type == "ESCALATION":
            return self._create_escalation_email(ticket, tone, recipient_context)
        else:
            return self._create_generic_email(ticket, tone, recipient_context)
    
    def _create_update_email(self, ticket: Ticket, tone: str, recipient_context: str) -> EmailDraft:
        """Create an update email"""
        greeting = self._get_greeting(tone, recipient_context)
        closing = self._get_closing(tone, recipient_context)
        
        subject = f"Update on Your Support Request - {ticket.title}"
        
        body = f"""{greeting}
        
Thank you for contacting us regarding "{ticket.title}".

We wanted to provide you with an update on your support request. Our technical team is currently investigating the issue you've reported:

{ticket.description}

We are working diligently to identify the root cause and implement a solution. Based on our initial analysis, we expect to have more information within the next 24-48 hours.

In the meantime, if you have any additional details that might help with our investigation, please don't hesitate to reach out.

We appreciate your patience and will keep you informed of our progress.

{closing}"""
        
        return EmailDraft(
            subject=subject,
            body=body,
            confidence_score=0.85,
            draft_reasoning="Pattern-based update email generated"
        )
    
    def _create_resolution_email(self, ticket: Ticket, tone: str, recipient_context: str) -> EmailDraft:
        """Create a resolution email"""
        greeting = self._get_greeting(tone, recipient_context)
        closing = self._get_closing(tone, recipient_context)
        
        subject = f"Resolved: {ticket.title}"
        
        body = f"""{greeting}

I'm pleased to inform you that we have resolved the issue reported in your support request "{ticket.title}".

Issue Details:
{ticket.description}

The resolution has been implemented and tested. You should now be able to proceed without the previously reported issues.

To verify the resolution:
1. Please test the affected functionality
2. Clear your browser cache if applicable  
3. Restart any relevant applications

If you continue to experience any issues or have questions about this resolution, please don't hesitate to contact us.

Thank you for your patience while we worked on this matter.

{closing}"""
        
        return EmailDraft(
            subject=subject,
            body=body,
            confidence_score=0.9,
            draft_reasoning="Pattern-based resolution email generated"
        )
    
    def _create_escalation_email(self, ticket: Ticket, tone: str, recipient_context: str) -> EmailDraft:
        """Create an escalation email"""
        greeting = self._get_greeting(tone, recipient_context)
        closing = self._get_closing(tone, recipient_context)
        
        subject = f"Escalation Notice: {ticket.title}"
        
        body = f"""{greeting}

I wanted to personally reach out regarding your support request "{ticket.title}".

Your case has been escalated to our senior technical team for priority attention due to the complexity of the issue:

{ticket.description}

A specialist will be assigned to work on this matter and will contact you within the next 4 hours with either a resolution or a detailed action plan.

We understand the importance of resolving this quickly and appreciate your patience as we work to provide the best possible solution.

{closing}"""
        
        return EmailDraft(
            subject=subject,
            body=body,
            confidence_score=0.8,
            draft_reasoning="Pattern-based escalation email generated"
        )
    
    def _create_generic_email(self, ticket: Ticket, tone: str, recipient_context: str) -> EmailDraft:
        """Create a generic support email"""
        greeting = self._get_greeting(tone, recipient_context)
        closing = self._get_closing(tone, recipient_context)
        
        subject = f"Re: {ticket.title}"
        
        body = f"""{greeting}

Thank you for contacting support regarding "{ticket.title}".

We have received your request and our technical team is reviewing the details:

{ticket.description}

We will investigate this matter and provide you with an update soon. Our goal is to resolve your issue as quickly as possible while ensuring a thorough solution.

If you have any additional information that might be helpful, please feel free to reply to this message.

{closing}"""
        
        return EmailDraft(
            subject=subject,
            body=body,
            confidence_score=0.7,
            draft_reasoning="Pattern-based generic email generated"
        )
    
    def _get_greeting(self, tone: str, recipient_context: str) -> str:
        """Get appropriate greeting based on tone and context"""
        if tone == "formal":
            if recipient_context == "executive":
                return "Dear Sir/Madam,"
            else:
                return "Dear Valued Customer,"
        elif tone == "friendly":
            return "Hello!"
        else:  # professional
            return "Dear Customer,"
    
    def _get_closing(self, tone: str, recipient_context: str) -> str:
        """Get appropriate closing based on tone and context"""
        if tone == "formal":
            return "Respectfully,\\nTechnical Support Team"
        elif tone == "friendly":
            return "Warm regards,\\nYour Support Team"
        else:  # professional
            return "Best regards,\\nCustomer Support Team"
    
    def _create_email_prompt(self, draft_request: EmailDraftRequest) -> str:
        """Create the email generation prompt"""
        resolution = draft_request.resolution_option
        
        return f"""
Draft a professional customer support email response based on the following information:

TICKET DETAILS:
- Ticket ID: {draft_request.ticket_id}
- Customer Email: {draft_request.recipient_email}

SELECTED RESOLUTION:
- Title: {resolution.title}
- Description: {resolution.description}
- Estimated Time: {resolution.estimated_time}
- Risk Level: {resolution.risk_level}
- Reasoning: {resolution.reasoning}

REQUIREMENTS:
1. Include a warm, professional greeting
2. Acknowledge the customer's issue with empathy
3. Express gratitude for their patience
4. Provide clear, step-by-step action items based on the resolution
5. Set appropriate expectations (timeline, next steps)
6. Professional closing with contact information for follow-up
7. Use clear, non-technical language where possible

Please format your response as JSON:
{{
    "subject": "Clear, specific subject line",
    "body": "Complete email body with proper formatting",
    "confidence_score": 0.85,
    "draft_reasoning": "Brief explanation of the approach taken"
}}

The email should be professional, helpful, and instill confidence in the solution provided.
"""
    
    def _parse_email_response(self, response_text: str) -> EmailDraft:
        """Parse LLM response into EmailDraft object"""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            response_data = json.loads(json_text)
            
            return EmailDraft(
                subject=response_data.get("subject", "Re: Your Support Request"),
                body=response_data.get("body", "Thank you for your inquiry. We are working on your request."),
                confidence_score=response_data.get("confidence_score", 0.5),
                draft_reasoning=response_data.get("draft_reasoning", "Standard email template")
            )
            
        except Exception as e:
            print(f"Error parsing email response: {str(e)}")
            return EmailDraft(
                subject="Re: Your Support Request",
                body="Thank you for contacting support. We are reviewing your request and will provide an update soon.",
                confidence_score=0.3,
                draft_reasoning="Fallback due to parsing error"
            )
    
    async def _create_audit_log(self, 
                              draft_request: EmailDraftRequest,
                              email_draft: EmailDraft,
                              db: Session) -> AIAuditLog:
        """Create audit log entry for email generation"""
        try:
            input_json = {
                "ticket_id": str(draft_request.ticket_id),
                "recipient_email": draft_request.recipient_email,
                "resolution_option": {
                    "title": draft_request.resolution_option.title,
                    "description": draft_request.resolution_option.description,
                    "confidence_score": draft_request.resolution_option.confidence_score,
                    "reasoning": draft_request.resolution_option.reasoning,
                    "estimated_time": draft_request.resolution_option.estimated_time,
                    "risk_level": draft_request.resolution_option.risk_level
                }
            }
            
            output_json = {
                "subject": email_draft.subject,
                "body": email_draft.body,
                "confidence_score": email_draft.confidence_score,
                "draft_reasoning": email_draft.draft_reasoning
            }
            
            confidence_json = {
                "email_confidence": email_draft.confidence_score,
                "resolution_confidence": draft_request.resolution_option.confidence_score
            }
            
            audit_log = AIAuditLog(
                ticket_id=draft_request.ticket_id,
                agent_name=self.agent_name,
                model_name=openai_service.model,
                input_json=input_json,
                output_json=output_json,
                confidence_json=confidence_json,
                supporting_incident_ids=None,
                was_used=False  # Will be updated when email is approved and sent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            return audit_log
            
        except Exception as e:
            print(f"Error creating email audit log: {str(e)}")
            db.rollback()
            raise e
    
    async def approve_and_send_email(self, 
                                   email_id: uuid.UUID,
                                   db: Session) -> bool:
        """Mark email as approved (actual sending would integrate with email service)"""
        try:
            # Update email status to APPROVED
            email = db.query(Email).filter(Email.email_id == email_id).first()
            if not email:
                raise ValueError(f"Email {email_id} not found")
            
            email.type = "APPROVED"
            
            # Update audit log to mark as used
            audit_log = db.query(AIAuditLog).filter(
                AIAuditLog.ticket_id == email.ticket_id,
                AIAuditLog.agent_name == self.agent_name
            ).order_by(AIAuditLog.created_at.desc()).first()
            
            if audit_log:
                audit_log.was_used = True
            
            db.commit()
            
            # Here you would integrate with an actual email service
            # For now, we'll just log that the email was "sent"
            print(f"Email {email_id} approved and ready to send")
            
            return True
            
        except Exception as e:
            print(f"Error approving email: {str(e)}")
            db.rollback()
            return False

# Global instance
comm_coach = CommCoachAgent()
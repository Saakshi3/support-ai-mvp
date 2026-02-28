from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
from app.config import OPENAI_ENDPOINT, OPENAI_API_KEY, LLM_MODEL, LLM_API_VERSION

class OpenAIService:
    """Service for interacting with Azure OpenAI"""
    
    def __init__(self):
        self._client = None
        self.model = LLM_MODEL
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                self._client = AzureOpenAI(
                    azure_endpoint=OPENAI_ENDPOINT,
                    api_key=OPENAI_API_KEY,
                    api_version=LLM_API_VERSION,
                    # Remove any problematic arguments
                )
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                # Don't set to None, set to a mock client flag
                self._client = False
        return self._client if self._client is not False else None
    
    async def generate_completion(self, 
                                messages: List[Dict[str, str]], 
                                temperature: float = 0.7,
                                max_tokens: int = 1000) -> str:
        """Generate a completion using the configured LLM"""
        if not self.client:
            # Return a mock response for testing
            return "Mock AI response (OpenAI client not available)"
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating completion: {str(e)}")
            return f"Error: Could not generate AI response - {str(e)}"
    
    async def generate_structured_completion(self, 
                                           messages: List[Dict[str, str]], 
                                           functions: List[Dict[str, Any]],
                                           temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a structured completion with function calling"""
        if not self.client:
            # Return a mock response for testing
            return {"content": "Mock structured response (OpenAI client not available)"}
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=temperature
            )
            
            choice = response.choices[0]
            if choice.message.function_call:
                return {
                    "function_call": {
                        "name": choice.message.function_call.name,
                        "arguments": choice.message.function_call.arguments
                    }
                }
            else:
                return {
                    "content": choice.message.content
                }
        except Exception as e:
            print(f"Error generating structured completion: {str(e)}")
            return {"content": f"Error: Could not generate structured response - {str(e)}"}

# Global instance - lazy initialization
openai_service = OpenAIService()
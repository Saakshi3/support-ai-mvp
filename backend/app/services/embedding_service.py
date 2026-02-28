import os
import numpy as np
from openai import AzureOpenAI
from typing import List, Optional
from app.config import OPENAI_ENDPOINT, OPENAI_API_KEY, LLM_API_VERSION

class EmbeddingService:
    """Service for generating embeddings using OpenAI's text-embedding model"""
    
    def __init__(self):
        self._client = None
        self.embedding_model = "text-embedding-ada-002"  # Standard embedding model
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                self._client = AzureOpenAI(
                    azure_endpoint=OPENAI_ENDPOINT,
                    api_key=OPENAI_API_KEY,
                    api_version=LLM_API_VERSION
                )
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                # Return a mock client for now
                self._client = None
        return self._client
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.client:
            # Return a dummy embedding for testing
            return [0.0] * 1536
            
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return [0.0] * 1536  # Fallback dummy embedding
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.client:
            # Return dummy embeddings for testing
            return [[0.0] * 1536 for _ in texts]
            
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 1536 for _ in texts]  # Fallback dummy embeddings
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a = np.array(embedding1)
        b = np.array(embedding2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def prepare_text_for_embedding(self, 
                                  title: str, 
                                  description: str, 
                                  resolution: Optional[str] = None) -> str:
        """Prepare ticket text for embedding generation"""
        text_parts = [f"Title: {title}", f"Description: {description}"]
        if resolution:
            text_parts.append(f"Resolution: {resolution}")
        return " | ".join(text_parts)

# Global instance - lazy initialization
embedding_service = EmbeddingService()
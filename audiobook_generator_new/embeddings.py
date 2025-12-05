# [file name]: embeddings.py
# [file content begin]
import os
import numpy as np
from typing import List

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI or fallback to a simple method."""
    # Try OpenAI first if available
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"OpenAI embedding failed: {e}, using fallback")
    
    # Fallback: simple TF-IDF like embedding (very basic)
    return fallback_embedding(text)

def fallback_embedding(text: str) -> List[float]:
    """Simple fallback embedding using word frequency."""
    words = text.lower().split()
    if not words:
        return [0.0] * 100  # Return zero vector for empty text
    
    # Create a simple embedding by averaging word hashes
    embedding = np.zeros(100)
    for word in words:
        # Use hash to create a pseudo-embedding
        hash_val = hash(word) % 1000
        word_vec = np.random.RandomState(hash_val).randn(100)
        embedding += word_vec
    
    return (embedding / len(words)).tolist()

def split_text_into_chunks(text: str, chunk_size: int = 1000) -> List[str]:
    """Split text into chunks for embedding."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
# [file content end]
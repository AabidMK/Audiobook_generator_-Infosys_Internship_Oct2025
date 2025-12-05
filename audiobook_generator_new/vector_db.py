# [file name]: vector_db.py
# [file content begin]
import os
import pickle
import tempfile
from typing import List, Tuple
import numpy as np

class SimpleVectorDB:
    """A simple in-memory vector database for storing document embeddings."""
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.db_path = os.path.join(tempfile.gettempdir(), "audiobook_vectordb.pkl")
        self.load_db()
    
    def load_db(self):
        """Load existing database from file."""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.embeddings = data.get('embeddings', [])
        except Exception as e:
            print(f"Error loading vector DB: {e}")
            self.documents = []
            self.embeddings = []
    
    def save_db(self):
        """Save database to file."""
        try:
            with open(self.db_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'embeddings': self.embeddings
                }, f)
        except Exception as e:
            print(f"Error saving vector DB: {e}")
    
    def add_document(self, text: str, embedding: List[float]):
        """Add a document and its embedding to the database."""
        self.documents.append(text)
        self.embeddings.append(embedding)
        self.save_db()
    
    def similarity_search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, float]]:
        """Find most similar documents using cosine similarity."""
        if not self.embeddings:
            return []
        
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(self.embeddings)
        
        # Calculate cosine similarities
        similarities = np.dot(doc_vecs, query_vec) / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
        )
        
        # Get top_k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return relevant results
                results.append((self.documents[idx], float(similarities[idx])))
        
        return results
    
    def clear_db(self):
        """Clear all documents from the database."""
        self.documents = []
        self.embeddings = []
        self.save_db()
# [file content end]
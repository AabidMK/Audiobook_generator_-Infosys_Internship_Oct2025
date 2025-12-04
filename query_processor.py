"""
Query Processor Module
Handles query embedding generation and similarity search in vector database
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer


class QueryProcessor:
    """Process user queries and perform similarity search in vector DB"""
    
    def __init__(self, 
                 persist_dir: str = "vector_store",
                 collection_name: str = "audiobook_embeddings",
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the query processor
        
        Args:
            persist_dir: Directory where Chroma DB is persisted
            collection_name: Name of the Chroma collection
            model_name: Sentence transformer model for query embeddings
        """
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.model_name = model_name
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Load or get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Try to list available collections for better error message
            try:
                collections = self.client.list_collections()
                collection_names = [c.name for c in collections]
                if collection_names:
                    raise ValueError(
                        f"Collection '{collection_name}' not found in {persist_dir}.\n"
                        f"Available collections: {', '.join(collection_names)}\n"
                        f"Please use --collection to specify the correct collection name, "
                        f"or store embeddings first using: python store_embeddings.py <csv_file>"
                    )
                else:
                    raise ValueError(
                        f"Collection '{collection_name}' not found in {persist_dir}.\n"
                        f"No collections found. Please store embeddings first using:\n"
                        f"  python store_embeddings.py <csv_file>"
                    )
            except Exception:
                raise ValueError(
                    f"Collection '{collection_name}' not found in {persist_dir}.\n"
                    f"Please store embeddings first using: python store_embeddings.py <csv_file>"
                )
        
        # Load embedding model
        print(f"Loading embedding model: {model_name}...")
        self.embedding_model = SentenceTransformer(model_name)
        print("Model loaded successfully!")
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a user query
        
        Args:
            query: User's query text
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar text chunks in vector database
        
        Args:
            query: User's query text
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries containing:
            - text: The text chunk
            - distance: Similarity distance (lower is more similar)
            - metadata: Any associated metadata
        """
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Search in Chroma DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'distances', 'metadatas']
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        return formatted_results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Get formatted context string from search results
        
        Args:
            query: User's query text
            top_k: Number of top results to include
            
        Returns:
            Formatted context string with retrieved text chunks
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return "No relevant context found in the document."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Chunk {i}]\n{result['text']}\n")
        
        return "\n".join(context_parts)


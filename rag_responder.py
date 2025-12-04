"""
RAG (Retrieval-Augmented Generation) Responder Module
Generates LLM responses using retrieved context from vector database
"""

import os
import google.generativeai as genai
from query_processor import QueryProcessor
from typing import Optional, List, Dict


class RAGResponder:
    """Generate LLM responses using RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 persist_dir: str = "vector_store",
                 collection_name: str = "audiobook_embeddings",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 llm_model: str = "gemini-2.5-flash"):
        """
        Initialize the RAG responder
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY env var)
            persist_dir: Directory where Chroma DB is persisted
            collection_name: Name of the Chroma collection
            embedding_model: Sentence transformer model for embeddings
            llm_model: Gemini model to use for generation
        """
        # Initialize Gemini API
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google Gemini API key is required. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )
        
        genai.configure(api_key=self.api_key)
        
        # Try to use the specified model, with fallbacks
        try:
            self.llm_model = genai.GenerativeModel(llm_model)
        except:
            try:
                self.llm_model = genai.GenerativeModel('gemini-2.5-pro')
            except:
                self.llm_model = genai.GenerativeModel('gemini-pro-latest')
        
        # Initialize query processor for vector search
        self.query_processor = QueryProcessor(
            persist_dir=persist_dir,
            collection_name=collection_name,
            model_name=embedding_model
        )
    
    def generate_response(self,
                         query: str,
                         top_k: int = 5,
                         system_prompt: Optional[str] = None) -> Dict:
        """
        Generate response to user query using RAG
        
        Args:
            query: User's query
            top_k: Number of top chunks to retrieve
            system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary containing:
            - response: LLM generated response
            - context_chunks: Retrieved context chunks
            - num_chunks: Number of chunks used
        """
        # Retrieve relevant context from vector DB
        print(f"Searching for relevant context (top {top_k} chunks)...")
        context_chunks = self.query_processor.search(query, top_k=top_k)
        
        if not context_chunks:
            return {
                'response': "I couldn't find any relevant information in the document to answer your query.",
                'context_chunks': [],
                'num_chunks': 0
            }
        
        # Format context
        context_text = self.query_processor.get_context(query, top_k=top_k)
        
        # Create prompt
        if not system_prompt:
            system_prompt = """You are a helpful assistant that answers questions based on the provided document context.

Instructions:
- Answer the user's question using ONLY the information provided in the context below
- If the context doesn't contain enough information to answer the question, say so clearly
- Rephrase and summarize the information in a clear, conversational manner
- Do not make up information that isn't in the context
- If multiple relevant chunks are provided, synthesize the information from all of them
- Keep your response concise but complete"""
        
        full_prompt = f"""{system_prompt}

Context from document:
{context_text}

User Question: {query}

Answer:"""
        
        # Generate response using Gemini
        print("Generating response using Gemini LLM...")
        try:
            response = self.llm_model.generate_content(full_prompt)
            
            if response.text:
                return {
                    'response': response.text.strip(),
                    'context_chunks': context_chunks,
                    'num_chunks': len(context_chunks)
                }
            else:
                return {
                    'response': "Sorry, I couldn't generate a response. Please try again.",
                    'context_chunks': context_chunks,
                    'num_chunks': len(context_chunks)
                }
        except Exception as e:
            return {
                'response': f"Error generating response: {str(e)}",
                'context_chunks': context_chunks,
                'num_chunks': len(context_chunks)
            }
    
    def query(self, user_query: str, top_k: int = 5) -> str:
        """
        Simple query interface that returns just the response text
        
        Args:
            user_query: User's query
            top_k: Number of top chunks to retrieve
            
        Returns:
            Response text
        """
        result = self.generate_response(user_query, top_k=top_k)
        return result['response']


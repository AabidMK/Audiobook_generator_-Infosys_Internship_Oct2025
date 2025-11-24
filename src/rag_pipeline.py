# rag_pipeline.py
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np

class RAGPipeline:
    def __init__(self, collection_name="audiobook_embeddings", chroma_path="./chroma_db"):
        """
        Initialize RAG Pipeline
        """
        print("🚀 Initializing RAG Pipeline...")
        
        # Initialize embedding model FIRST
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            raise
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=chroma_path)
            print("✅ ChromaDB client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB: {e}")
            raise
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ Connected to collection: {collection_name}")
        except Exception as e:
            print(f"❌ Collection not found: {e}")
            print("💡 Run: python setup_chroma.py")
            raise
        
        # Initialize LLM
        self.llm = self.initialize_llm()  # ✅ Correct variable name
        print("✅ RAG Pipeline initialized successfully!\n")

    def initialize_llm(self):
        """
        Initialize Smart Local LLM
        """
        try:
            from LLM import SmartLocalLLM
            print("✅ Initializing Smart Local LLM...")
            return SmartLocalLLM()
        except Exception as e:
            print(f"⚠ Error loading Local LLM: {e}")
            return self.FallbackLLM()

    def generate_query_embedding(self, query):
        """
        Step 1: Generate embedding for user query
        """
        print(f"🔍 Generating embedding for query...")
        try:
            query_embedding = self.embedding_model.encode([query])
            print("✅ Query embedding generated")
            return query_embedding.tolist()[0]
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise

    def similarity_search(self, query, top_k=5):
        """
        Step 2: Perform similarity search and retrieve top K chunks
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_query_embedding(query)
            
            # Search in ChromaDB
            print(f"🔎 Performing similarity search (top {top_k})...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if results and results['documents']:
                print(f"✅ Found {len(results['documents'][0])} relevant chunks")
            else:
                print("❌ No documents found in search results")
                
            return results
            
        except Exception as e:
            print(f"❌ Error in similarity search: {e}")
            return None

    def format_context(self, search_results):
        """
        Step 3: Format retrieved chunks into readable context
        """
        try:
            if not search_results or not search_results.get('documents') or not search_results['documents'][0]:
                return "No relevant context found."
            
            documents = search_results['documents'][0]
            metadatas = search_results.get('metadatas', [[]])[0] if search_results.get('metadatas') else [{}] * len(documents)
            distances = search_results.get('distances', [[]])[0] if search_results.get('distances') else [0] * len(documents)
            
            context_parts = []
            context_parts.append("📚 *Retrieved Relevant Information:*\n")
            
            for i, doc in enumerate(documents):
                # Safely get metadata
                metadata = metadatas[i] if i < len(metadatas) else {}
                source = metadata.get('source', 'unknown') if isinstance(metadata, dict) else 'unknown'
                
                # Safely get distance
                distance = distances[i] if i < len(distances) else 0
                similarity_score = 1 - distance if isinstance(distance, (int, float)) else 'N/A'
                
                context_parts.append(f"*Chunk {i+1}* (Similarity: {similarity_score:.3f})")
                context_parts.append(f"Source: {source}")
                context_parts.append(f"Content: {doc}\n")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"❌ Error formatting context: {e}")
            return f"Error formatting context: {e}"

    def create_llm_prompt(self, query, context):
        """
        Step 4: Create optimized prompt for LLM
        """
        prompt = f"""Please answer the user's question based ONLY on the following context retrieved from documents.

USER QUESTION: {query}

RETRIEVED CONTEXT:
{context}

INSTRUCTIONS:
1. Answer the question using ONLY the information from the context above
2. If the context doesn't contain relevant information, say: "I don't have enough information in the provided documents to answer this question accurately."
3. Be concise and factual (1-2 paragraphs maximum)
4. Do not add any information not present in the context
5. If you reference specific information, mention that it comes from the documents

ANSWER:"""
        
        return prompt

    def get_llm_response(self, prompt):
        """
        Step 5: Get response from LLM - FIXED TYPO
        """
        try:
            print("🤖 Generating response with Local LLM...")
            response = self.llm.generate_response(prompt)  # ✅ FIXED: 'llm' not 'Ilm'
            return response
        except Exception as e:
            return f"Error generating LLM response: {e}"

    def process_query(self, query, top_k=5):
        """
        Complete RAG Pipeline
        """
        print(f"\n{'='*50}")
        print(f"🎯 PROCESSING QUERY: '{query}'")
        print(f"{'='*50}")
        
        try:
            # Step 1 & 2: Generate embedding and similarity search
            search_results = self.similarity_search(query, top_k)
            
            if not search_results or not search_results.get('documents') or not search_results['documents'][0]:
                return "❌ No relevant information found in the documents for your query."
            
            # Step 3: Format context
            print("📋 Formatting context...")
            context = self.format_context(search_results)
            
            # Debug: Show what we retrieved
            print(f"📄 Retrieved {len(search_results['documents'][0])} chunks")
            for i, doc in enumerate(search_results['documents'][0][:2]):
                print(f"   Chunk {i+1}: {doc[:100]}...")
            
            # Step 4: Create prompt
            prompt = self.create_llm_prompt(query, context)
            
            # Step 5: Get LLM response
            response = self.get_llm_response(prompt)
            
            print("✅ Response generated successfully!")
            return response
            
        except Exception as e:
            print(f"❌ Error in process_query: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error processing query: {e}"

    def interactive_mode(self):
        """
        Interactive mode for testing
        """
        print("\n🎮 *INTERACTIVE RAG MODE*")
        print("Type your questions (type 'exit' to quit)")
        print("-" * 50)
        
        while True:
            query = input("\n💬 Your question: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                continue
                
            response = self.process_query(query)
            print(f"\n🤖 *ANSWER:*\n{response}\n")

    class FallbackLLM:
        """
        Fallback LLM implementation
        """
        def generate_response(self, prompt):
            return "Local LLM is not available. Please check the LLM.py file."

def main():
    """
    Main function
    """
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Start interactive mode
        rag.interactive_mode()
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG pipeline: {e}")
        print("\n💡 *Troubleshooting Steps:*")
        print("1. Run: python setup_chroma.py")
        print("2. Check if LLM.py exists in the same directory")
        print("3. Verify chroma_db directory exists")

if __name__ == "__main__":
    main()
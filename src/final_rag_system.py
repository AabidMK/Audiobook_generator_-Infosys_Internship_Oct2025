"""
AUDIOBOOK RAG SYSTEM - CORRECTED VERSION
Fixes all import and path issues
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

print("🎧 AUDIOBOOK RAG SYSTEM - CORRECTED VERSION")
print("=" * 60)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class AudiobookRAGSystem:
    def __init__(self):
        # FIXED: Use absolute paths
        self.script_dir = Path(__file__).parent
        self.documents_path = self.script_dir / "documents"
        self.chroma_db_path = self.script_dir / "chroma_db"
        
        # Create directories if they don't exist
        self.documents_path.mkdir(exist_ok=True)
        self.chroma_db_path.mkdir(exist_ok=True)
        
        logger.info(f"📁 Documents folder: {self.documents_path}")
        logger.info(f"💾 Chroma DB folder: {self.chroma_db_path}")
        
        # Check for PDFs
        self.pdf_files = list(self.documents_path.glob("*.pdf"))
        if not self.pdf_files:
            logger.warning(f"⚠ No PDF files found in {self.documents_path}")
            logger.info("💡 Please add PDF files to the 'documents' folder")
        else:
            logger.info(f"✅ Found {len(self.pdf_files)} PDF files")
            for pdf in self.pdf_files[:5]:  # Show first 5
                logger.info(f"   - {pdf.name}")
            if len(self.pdf_files) > 5:
                logger.info(f"   ... and {len(self.pdf_files) - 5} more")
    
    
    def setup_document_loader(self) -> Optional[List]:
        """Load PDF documents from the documents folder"""
        logger.info("\n📄 STEP 1: LOADING DOCUMENTS")
        logger.info("-" * 30)
        
        if not self.pdf_files:
            logger.error("❌ No PDF files found to process!")
            return None
        
        all_documents = []
        
        try:
            # CORRECTED: Use new import structure
            from langchain_community.document_loaders import PyPDFLoader
            
            for pdf_file in self.pdf_files:
                logger.info(f"📖 Loading: {pdf_file.name}")
                try:
                    loader = PyPDFLoader(str(pdf_file))
                    documents = loader.load()
                    all_documents.extend(documents)
                    logger.info(f"   ✅ Loaded {len(documents)} pages")
                except Exception as e:
                    logger.error(f"   ❌ Error loading {pdf_file.name}: {e}")
            
            logger.info(f"📊 Total documents loaded: {len(all_documents)}")
            return all_documents
            
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.info("💡 Install required packages: pip install langchain-community pypdf")
            return None
    
    def split_documents(self, documents: List) -> Optional[List]:
        """Split documents into chunks"""
        logger.info("\n✂ STEP 2: SPLITTING DOCUMENTS")
        logger.info("-" * 30)
        
        if not documents:
            logger.error("❌ No documents to split!")
            return None
        
        try:
            # CORRECTED: Use new import structure
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                add_start_index=True,
            )
            
            splits = text_splitter.split_documents(documents)
            logger.info(f"✅ Created {len(splits)} chunks from {len(documents)} documents")
            
            if splits:
                logger.info(f"📝 Sample chunk (first 200 chars): {splits[0].page_content[:200]}...")
            
            return splits
            
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.info("💡 Install: pip install langchain-text-splitters")
            return None
    
    def setup_embeddings(self):
        """Setup embeddings using Ollama"""
        logger.info("\n🔧 STEP 3: SETTING UP EMBEDDINGS")
        logger.info("-" * 30)
        
        try:
            # Check if Ollama is running
            import requests
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ Ollama is running")
                    
                    # Check for embedding models
                    models = response.json().get('models', [])
                    model_names = [m.get('name', '') for m in models]
                    
                    # Look for recommended models
                    recommended_models = ["nomic-embed-text", "all-minilm", "llama2", "mistral"]
                    found_models = [m for m in recommended_models if any(m in name for name in model_names)]
                    
                    if found_models:
                        model_to_use = found_models[0]
                        logger.info(f"✅ Found model: {model_to_use}")
                    else:
                        model_to_use = "nomic-embed-text"
                        logger.warning(f"⚠ No recommended models found. Will try: {model_to_use}")
                        logger.info("💡 Run: ollama pull nomic-embed-text")
                else:
                    logger.warning("⚠ Ollama responded with unexpected status")
                    model_to_use = "nomic-embed-text"
                    
            except requests.ConnectionError:
                logger.error("❌ Cannot connect to Ollama on port 11434")
                logger.info("💡 Please ensure Ollama is running:")
                logger.info("   1. Download from: https://ollama.ai/")
                logger.info("   2. Install and run: ollama serve")
                logger.info("   3. In another terminal: ollama pull nomic-embed-text")
                return None
            
            # Setup embeddings
            try:
                from langchain_community.embeddings import OllamaEmbeddings
                
                embeddings = OllamaEmbeddings(
                    model="all-minilm",
                    base_url="http://localhost:11434"
                )
                
                # Test the embeddings
                test_text = "Hello from Audiobook RAG System"
                test_vector = embeddings.embed_query(test_text)
                logger.info(f"✅ Embeddings initialized with model: {model_to_use}")
                logger.info(f"📐 Embedding dimension: {len(test_vector)}")
                
                return embeddings
                
            except ImportError as e:
                logger.error(f"❌ Import error: {e}")
                logger.info("💡 Install: pip install langchain-community")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error setting up embeddings: {e}")
            return None
    
    def create_vector_store(self, splits, embeddings):
        """Create Chroma vector store"""
        logger.info("\n💾 STEP 4: CREATING VECTOR STORE")
        logger.info("-" * 30)
        
        if not splits:
            logger.error("❌ No documents to add to vector store")
            return None
        
        if not embeddings:
            logger.error("❌ No embeddings available")
            return None
        
        try:
            from langchain_chroma import Chroma
            
            # Create or load vector store
            vector_store = Chroma(
                collection_name="audiobook_rag",
                embedding_function=embeddings,
                persist_directory=str(self.chroma_db_path),
            )
            
            # Add documents
            logger.info(f"📚 Adding {len(splits)} documents to vector store...")
            vector_store.add_documents(documents=splits)
            
            logger.info(f"✅ Vector store created with {len(splits)} documents")
            logger.info(f"💾 Saved to: {self.chroma_db_path}")
            
            return vector_store
            
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.info("💡 Install: pip install langchain-chroma chromadb")
            return None
    
    def setup_complete_system(self):
        """Complete system setup"""
        logger.info("\n🔧 COMPLETE SYSTEM SETUP")
        logger.info("=" * 50)
        
        # Step 1: Load documents
        documents = self.setup_document_loader()
        if not documents:
            logger.error("❌ SYSTEM SETUP FAILED at step 1")
            return None
        
        # Step 2: Split documents
        splits = self.split_documents(documents)
        if not splits:
            logger.error("❌ SYSTEM SETUP FAILED at step 2")
            return None
        
        # Step 3: Setup embeddings
        embeddings = self.setup_embeddings()
        if not embeddings:
            logger.error("❌ SYSTEM SETUP FAILED at step 3")
            return None
        
        # Step 4: Create vector store
        vector_store = self.create_vector_store(splits, embeddings)
        if not vector_store:
            logger.error("❌ SYSTEM SETUP FAILED at step 4")
            return None
        
        logger.info("\n🎉 SYSTEM SETUP COMPLETE!")
        logger.info("=" * 50)
        return vector_store
    
    def search_documents(self, vector_store, query: str, k: int = 3):
        """Search documents using semantic search"""
        if not vector_store:
            logger.error("❌ Vector store not initialized")
            return
        
        logger.info(f"\n🔍 SEARCHING: '{query}'")
        logger.info("-" * 40)
        
        try:
            results = vector_store.similarity_search(query, k=k)
            
            logger.info(f"✅ Found {len(results)} relevant results:")
            for i, doc in enumerate(results):
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', 'N/A')
                
                logger.info(f"\n{i+1}. 📄 Source: {Path(source).name} (Page {page})")
                logger.info(f"   📝 Content: {doc.page_content}")
                
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return None
    
    def search_with_scores(self, vector_store, query: str, k: int = 3):
        """Search with similarity scores"""
        if not vector_store:
            logger.error("❌ Vector store not initialized")
            return
        
        logger.info(f"\n🎯 SEARCH WITH SCORES: '{query}'")
        logger.info("-" * 40)
        
        try:
            results = vector_store.similarity_search_with_score(query, k=k)
            
            for i, (doc, score) in enumerate(results):
                source = doc.metadata.get('source', 'Unknown')
                logger.info(f"{i+1}. Score: {score:.4f} | 📄 {Path(source).name}")
                logger.info(f"   📝 {doc.page_content[:150]}...\n")
                
            return results
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🎧 AUDIOBOOK RAG SYSTEM - READY TO USE")
    print("=" * 60)
    
    # Create system
    system = AudiobookRAGSystem()
    
    # Setup complete system
    vector_store = system.setup_complete_system()
    
    if not vector_store:
        print("\n❌ SYSTEM SETUP FAILED!")
        print("\n💡 PLEASE CHECK:")
        print("1. Add PDF files to 'documents' folder")
        print("2. Ensure Ollama is running: ollama serve")
        print("3. Pull embedding model: ollama pull nomic-embed-text")
        print("4. Install required packages (see errors above)")
        return
    
    # Interactive search
    print("\n" + "=" * 60)
    print("🔍 SEMANTIC SEARCH ENGINE READY!")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your question to search documents")
    print("  - Type 'score <query>' for search with similarity scores")
    print("  - Type 'exit' to quit")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n🔍 Enter query: ").strip()
            
            if user_input.lower() == 'exit':
                print("\n👋 Thank you for using Audiobook RAG System!")
                break
            elif user_input.lower() == 'list':
                # List available PDFs
                pdfs = list(Path("documents").glob("*.pdf"))
                if pdfs:
                    print(f"\n📚 Available PDFs ({len(pdfs)}):")
                    for pdf in pdfs:
                        print(f"  - {pdf.name}")
                else:
                    print("\n❌ No PDFs in documents folder")
            elif user_input.lower().startswith('score '):
                query = user_input[6:].strip()
                if query:
                    system.search_with_scores(vector_store, query)
                else:
                    print("❌ Please enter a query after 'score'")
            elif user_input:
                system.search_documents(vector_store, user_input)
            else:
                print("💡 Please enter a search query or command")
                
        except KeyboardInterrupt:
            print("\n\n👋 Session ended by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    # Check and install required packages
    required_packages = [
        "langchain-community",
        "langchain-text-splitters", 
        "langchain-chroma",
        "pypdf",
        "chromadb",
        "requests"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "langchain-community":
                __import__("langchain_community")
            elif package == "langchain-text-splitters":
                __import__("langchain_text_splitters")
            elif package == "langchain-chroma":
                __import__("langchain_chroma")
            else:
                __import__(package.replace("-", ""))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠ Missing packages: {', '.join(missing_packages)}")
        print("Installing required packages...")
        import subprocess
        for package in missing_packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package])
        print("✅ Packages installed. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Run main function
    main()
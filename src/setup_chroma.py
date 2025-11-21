# setup_chroma.py
import os
import subprocess
import sys

def setup_chromadb():
    """
    Step 4.1: Setup and verification script
    """
    print("🔧 ChromaDB Setup Script")
    print("=" * 50)
    
    # Check if ChromaDB is installed
    try:
        import chromadb
        print("✅ ChromaDB is installed")
    except ImportError:
        print("❌ ChromaDB not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chromadb"])
        print("✅ ChromaDB installed successfully")
    
    # Check for embedding files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'embedding' in f.lower()]
    
    if csv_files:
        print(f"✅ Found {len(csv_files)} embedding files:")
        for file in csv_files:
            print(f"   - {file}")
    else:
        print("❌ No embedding CSV files found")
        print("💡 Please run your LocalTextEmbedder first to generate embeddings")
        return
    
    # Test ChromaDB
    try:
        from chroma_integration import ChromaVectorDB
        db = ChromaVectorDB()
        print("✅ ChromaDB connection successful")
        
        # Test with first CSV file
        if csv_files:
            success = db.add_embeddings_from_csv(csv_files[0])
            if success:
                print("✅ ChromaDB integration working!")
            else:
                print("❌ Failed to add embeddings to ChromaDB")
    
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")

if __name__ == "__main__":
    setup_chromadb()
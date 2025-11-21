# chroma_pipeline.py
from chroma_integration import ChromaVectorDB
from sentence_transformers import SentenceTransformer
import os

class ChromaPipeline:
    def __init__(self):
        """
        Step 3.1: Initialize the complete pipeline
        """
        self.vector_db = ChromaVectorDB()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("🚀 ChromaDB Pipeline Initialized")
    
    def process_embedding_file(self, csv_file_path):
        """
        Step 3.2: Process embedding CSV and store in ChromaDB
        """
        print(f"\n📁 PROCESSING: {csv_file_path}")
        print("=" * 50)
        
        success = self.vector_db.add_embeddings_from_csv(csv_file_path)
        
        if success:
            count = self.vector_db.get_collection_info()
            print(f"\n✅ Processing complete! Stored {count} vectors in ChromaDB")
        else:
            print("❌ Processing failed")
        
        return success
    
    def demo_search(self, test_queries=None):
        """
        Step 3.3: Demonstrate search functionality
        """
        if test_queries is None:
            test_queries = [
                "machine learning",
                "artificial intelligence",
                "data analysis", 
                "computer science",
                "technology future"
            ]
        
        print(f"\n🎯 DEMO SEARCHES")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 40)
            
            results = self.vector_db.search_similar(query, self.embedder, top_k=3)
            
            if results:
                for result in results:
                    print(f"   #{result['rank']} (Similarity: {result['similarity_score']:.4f})")
                    print(f"      {result['text_preview']}")
            else:
                print("   No results found")
    
    def interactive_search(self):
        """
        Step 3.4: Interactive search interface
        """
        count = self.vector_db.get_collection_info()
        if count == 0:
            print("❌ No vectors in database. Please process embedding files first.")
            return
        
        print(f"\n🎯 INTERACTIVE CHROMADB SEARCH")
        print("=" * 60)
        print(f"Database has {count} vectors ready for search!")
        print("Commands:")
        print("  - Type your search query")
        print("  - Type 'stats' for database info") 
        print("  - Type 'exit' to quit")
        print("=" * 60)
        
        while True:
            user_input = input("\n🔍 Enter search query: ").strip()
            
            if user_input.lower() == 'exit':
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'stats':
                self.vector_db.get_collection_info()
                
            elif user_input:
                print(f"Searching for: '{user_input}'")
                results = self.vector_db.search_similar(user_input, self.embedder, top_k=5)
                
                if results:
                    print(f"\n📖 Found {len(results)} results:")
                    print("-" * 50)
                    
                    for result in results:
                        print(f"\n🏆 Rank #{result['rank']}")
                        print(f"   Similarity: {result['similarity_score']:.4f}")
                        print(f"   Text: {result['text']}")
                        print(f"   Length: {result['text_length']} chars")
                else:
                    print("❌ No results found. Try different keywords.")
    
    def batch_process_files(self, directory_path="."):
        """
        Step 3.5: Process all CSV files in a directory
        """
        csv_files = [f for f in os.listdir(directory_path) 
                    if f.endswith('.csv') and 'embedding' in f.lower()]
        
        if not csv_files:
            print("❌ No embedding CSV files found")
            return
        
        print(f"📁 Found {len(csv_files)} embedding files:")
        for file in csv_files:
            print(f"   - {file}")
        
        for csv_file in csv_files:
            file_path = os.path.join(directory_path, csv_file)
            self.process_embedding_file(file_path)

def main():
    """
    Step 3.6: Main execution function
    """
    pipeline = ChromaPipeline()
    
    print("🚀 CHROMADB AUDIOBOOK VECTOR DATABASE")
    print("=" * 60)
    
    # Option 1: Process specific file
    # pipeline.process_embedding_file("your_embedding_file.csv")
    
    # Option 2: Process all embedding files in current directory
    pipeline.batch_process_files()
    
    # Demo searches
    pipeline.demo_search()
    
    # Interactive search
    pipeline.interactive_search()

if __name__ == "__main__":
    main()
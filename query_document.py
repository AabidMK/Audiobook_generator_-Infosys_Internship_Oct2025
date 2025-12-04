"""
Query Document Script
CLI tool to query documents using RAG (Retrieval-Augmented Generation)
"""

import sys
import os
from rag_responder import RAGResponder


def main():
    """Main function for querying documents"""
    
    if len(sys.argv) < 2:
        print("Usage: python query_document.py <user_query> [options]")
        print("\nOptions:")
        print("  --api-key <key>          Google Gemini API key")
        print("  --top-k <number>         Number of top chunks to retrieve (default: 5)")
        print("  --collection <name>      Chroma collection name (default: audiobook_embeddings)")
        print("  --persist-dir <path>     Vector DB directory (default: vector_store)")
        print("\nExample:")
        print('  python query_document.py "What is Amazon RDS?"')
        print('  python query_document.py "Explain database services" --top-k 3')
        sys.exit(1)
    
    user_query = sys.argv[1]
    
    # Parse arguments
    api_key = None
    top_k = 5
    collection_name = "audiobook_embeddings"
    persist_dir = "vector_store"
    
    if '--api-key' in sys.argv:
        idx = sys.argv.index('--api-key')
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]
    
    if '--top-k' in sys.argv:
        idx = sys.argv.index('--top-k')
        if idx + 1 < len(sys.argv):
            try:
                top_k = int(sys.argv[idx + 1])
            except ValueError:
                print("Error: --top-k must be a number")
                sys.exit(1)
    
    if '--collection' in sys.argv:
        idx = sys.argv.index('--collection')
        if idx + 1 < len(sys.argv):
            collection_name = sys.argv[idx + 1]
    
    if '--persist-dir' in sys.argv:
        idx = sys.argv.index('--persist-dir')
        if idx + 1 < len(sys.argv):
            persist_dir = sys.argv[idx + 1]
    
    try:
        print("=" * 70)
        print("DOCUMENT QUERY SYSTEM (RAG)")
        print("=" * 70)
        print(f"Query: {user_query}")
        print(f"Retrieving top {top_k} relevant chunks...")
        print("=" * 70)
        print()
        
        # Initialize RAG responder
        responder = RAGResponder(
            api_key=api_key,
            persist_dir=persist_dir,
            collection_name=collection_name
        )
        
        # Generate response
        result = responder.generate_response(user_query, top_k=top_k)
        
        # Display results
        print("ANSWER:")
        print("-" * 70)
        print(result['response'])
        print("-" * 70)
        print()
        print(f"Based on {result['num_chunks']} relevant chunk(s) from the document.")
        
        if result['context_chunks']:
            print("\nRetrieved Context Chunks:")
            for i, chunk in enumerate(result['context_chunks'], 1):
                print(f"\n[Chunk {i}] (Distance: {chunk['distance']:.4f})")
                print(chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'])
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Generated embeddings: python generate_embeddings.py <text_file>")
        print("2. Stored embeddings in vector DB: python store_embeddings.py <csv_file>")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


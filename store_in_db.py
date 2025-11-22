import pandas as pd
import chromadb
import ast
import sys
import os

def store_embeddings(csv_path):
    # 1. Setup ChromaDB (Persistent storage)
    # This creates a folder named 'my_vectordb' in your current directory
    print("⚙️  Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="my_vectordb")
    
    # Create (or get) a collection. Think of this like a table in SQL.
    collection_name = "document_chunks"
    collection = client.get_or_create_collection(name=collection_name)
    
    # 2. Read the CSV data
    print(f"📖 Reading data from '{csv_path}'...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("❌ Error: CSV file not found.")
        return

    # 3. Prepare data for insertion
    print("🛠️  Processing data...")
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, row in df.iterrows():
        # IDs must be unique strings. We'll use the chunk_id.
        ids.append(str(row['chunk_id']))
        
        # The text content
        documents.append(row['text_chunk'])
        
        # CRITICAL STEP: Convert string "[0.1, 0.2]" back to list [0.1, 0.2]
        # When pandas reads lists from CSV, it sees them as Strings. 
        # ast.literal_eval fixes this safely.
        emb_list = ast.literal_eval(row['embedding'])
        embeddings.append(emb_list)
        
        # Metadata is useful for filtering later (e.g., page number, source file)
        metadatas.append({"source": csv_path, "chunk_id": row['chunk_id']})

    # 4. Add to ChromaDB
    # Chroma can handle batch additions automatically
    print(f"💾 Adding {len(documents)} chunks to the database...")
    try:
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print("-" * 40)
        print("✅ Success! Data stored in 'my_vectordb' folder.")
        print(f"Collection Name: {collection_name}")
        print(f"Total Items: {collection.count()}")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error adding to database: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python store_in_db.py <path_to_embeddings_csv>")
    else:
        store_embeddings(sys.argv[1])
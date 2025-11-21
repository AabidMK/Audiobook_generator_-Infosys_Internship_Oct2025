# chroma_integration.py
import chromadb
from chromadb.config import Settings
import numpy as np
import pandas as pd
import os
from datetime import datetime

class ChromaVectorDB:
    def __init__(self, persist_directory="./chroma_db"):
        """
        Step 2.1: Initialize ChromaDB client
        """
        print(f"🔧 Initializing ChromaDB at: {persist_directory}")
        
        # Create persistent client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(allow_reset=True)
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="audiobook_embeddings",
            metadata={
                "description": "Audiobook text embeddings",
                "created_at": datetime.now().isoformat(),
                "hnsw:space": "cosine"  # Use cosine similarity
            }
        )
        
        print("✅ ChromaDB initialized successfully")
        print(f"   Collection: {self.collection.name}")
    
    def add_embeddings_from_csv(self, csv_file_path):
        """
        Step 2.2: Load embeddings from CSV and add to ChromaDB
        """
        print(f"📁 Loading embeddings from: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"❌ File not found: {csv_file_path}")
            return False
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file_path)
            print(f"✅ CSV loaded: {df.shape}")
            
            # Extract data
            text_chunks = df['Text'].tolist()
            embedding_strings = df['Embedding'].tolist()
            
            # Convert embedding strings to vectors
            vectors = []
            valid_texts = []
            valid_indices = []
            
            for i, (text, embed_str) in enumerate(zip(text_chunks, embedding_strings)):
                try:
                    if pd.isna(embed_str) or embed_str == '':
                        continue
                    
                    # Convert string to numpy array
                    clean_str = embed_str.strip('[]()')
                    vector = np.fromstring(clean_str, sep=',')
                    
                    if len(vector) > 0 and not np.any(np.isnan(vector)):
                        vectors.append(vector.tolist())  # Convert to list for ChromaDB
                        valid_texts.append(text)
                        valid_indices.append(i)
                        
                except Exception as e:
                    print(f"⚠ Skipping chunk {i}: {e}")
                    continue
            
            print(f"🔄 Converted {len(vectors)} embeddings to vectors")
            
            # Create IDs
            ids = [f"chunk_{i}" for i in valid_indices]
            
            # Create metadata
            metadatas = [
                {
                    "chunk_id": i,
                    "text_length": len(text),
                    "source_file": csv_file_path,
                    "added_at": datetime.now().isoformat()
                }
                for i, text in zip(valid_indices, valid_texts)
            ]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=vectors,
                documents=valid_texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Successfully added {len(vectors)} vectors to ChromaDB")
            return True
            
        except Exception as e:
            print(f"❌ Error adding to ChromaDB: {e}")
            return False
    
    def search_similar(self, query_text, embedder, top_k=5):
        """
        Step 2.3: Semantic search using ChromaDB
        """
        print(f"🔍 Searching for: '{query_text}'")
        
        # Convert query to vector
        query_vector = embedder.encode([query_text])[0].tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # Convert distance to similarity score
                similarity_score = 1 - distance
                
                formatted_results.append({
                    'rank': i + 1,
                    'chunk_id': metadata.get('chunk_id', i),
                    'text': doc,
                    'similarity_score': round(similarity_score, 4),
                    'distance': round(distance, 4),
                    'text_length': metadata.get('text_length', len(doc)),
                    'text_preview': doc[:100] + '...' if len(doc) > 100 else doc
                })
        
        return formatted_results
    
    def get_collection_info(self):
        """
        Step 2.4: Get information about the collection
        """
        try:
            count = self.collection.count()
            print(f"📊 Collection Info:")
            print(f"   Total vectors: {count}")
            print(f"   Collection name: {self.collection.name}")
            return count
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return 0
    
    def delete_collection(self):
        """
        Step 2.5: Delete collection (for reset)
        """
        try:
            self.client.delete_collection(self.collection.name)
            print("🗑 Collection deleted")
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from google import genai
from google.genai import types
from typing import List
import chromadb

# --- CONFIGURATION ---
# IMPORTANT: Ensure GEMINI_API_KEY is set in your environment variables
EMBEDDING_MODEL = "gemini-embedding-001"
COLLECTION_NAME = "gemini_document_embeddings"
PERSIST_DIRECTORY = "my_vector_db"

CHUNK_SIZE_WORDS = 200      
OVERLAP_WORDS = 50          
# ---------------------------------------------------------------------

try:
    client = genai.Client()
except Exception as e:
    print("ERROR: Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set.")
    print(f"Details: {e}")
    exit()

# ---------------------------------------------------------------------

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> List[str]:
    """Splits text into overlapping chunks based on word count."""
    cleaned_text = text.replace('\r', '').strip()
    words = cleaned_text.split()
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk) 
        start += (chunk_size - overlap)
    
    return [c for c in chunks if len(c) > 20]


def generate_embeddings_and_populate_db():
    """Reads file, generates embeddings, and populates ChromaDB."""
    
    print("A file selection window will now pop up. Please select your raw text (.txt) file.")
    root = tk.Tk()
    root.withdraw() 
    
    input_file_path = filedialog.askopenfilename(
        title="Select the Text File to Embed",
        filetypes=[("Text files", "*.txt")]
    )

    if not input_file_path:
        print("No file selected. Exiting script.")
        return

    # 1. Read and Chunk Text
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        print(f"Reading input file: {input_file_path}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    text_chunks = split_into_chunks(raw_text, CHUNK_SIZE_WORDS, OVERLAP_WORDS)
    if not text_chunks:
        print("Error: Text file is empty or could not be chunked properly. Exiting.")
        return
        
    print(f"Document split into {len(text_chunks)} overlapping chunks.")
    
    # 2. Generate Embeddings using Gemini
    print("--- Calling Gemini API to generate embeddings (This may take a moment) ---")
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text_chunks
        )
        
        # 🎯 THE FIX: Extract the list of floats from the custom ContentEmbedding object
        raw_embeddings_list = response.embeddings
        embeddings_list = [emb.values for emb in raw_embeddings_list]
        
    except Exception as e:
        print(f"\nAPI Error during embedding call: {e}")
        print("Check your API key validity, internet connection, and usage limits.")
        return
        
        
    # 3. Populate ChromaDB
    print(f"Initializing ChromaDB and saving to directory: ./{PERSIST_DIRECTORY}")
    
    # Using PersistentClient to save the data to disk
    db_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Prepare data for ChromaDB format
    ids = [str(i) for i in range(len(text_chunks))] 
    
    print(f"Adding {len(text_chunks)} documents to the ChromaDB collection...")
    
    try:
        collection.add(
            embeddings=embeddings_list,
            documents=text_chunks,
            ids=ids
        )
    except Exception as e:
        print(f"ChromaDB Error: Failed to add documents. Details: {e}")
        return
    
    print("\n✅ Vector Database Creation Complete!")
    print(f"Database saved to the '{PERSIST_DIRECTORY}' folder.")
    print(f"Total documents in collection: {collection.count()}")


if __name__ == "__main__":
    generate_embeddings_and_populate_db()
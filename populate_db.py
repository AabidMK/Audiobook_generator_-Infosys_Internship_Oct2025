import pandas as pd
from ast import literal_eval
import chromadb 
import tkinter as tk
from tkinter import filedialog
import os
from typing import List, Dict, Any, Optional

# --- 1. Data Cleaning Function (FIXES 'literal_eval' AND INCONSISTENT DIMENSIONS) ---

def clean_embedding_string(s: Any) -> Optional[str]:
    """
    Cleans the embedding string precisely, handling NaNs and the 'values=[...)' format.
    Returns None if the input is genuinely unparseable.
    """
    if pd.isna(s):
        return None
        
    s = str(s).strip() 
    
    # 1. Remove the problematic 'values=[' prefix
    if s.startswith('values=['):
        s = s[len('values='):].strip()
    
    # 2. Remove a trailing ')' ONLY if the string does NOT end with ']'
    if s.endswith(')') and not s.endswith(']'):
        s = s[:-1].strip() 
        
    # 3. Ensure proper list enclosure (e.g., [1.2, 3.4])
    if not s.startswith('['):
        s = '[' + s
    if not s.endswith(']'):
        s = s + ']'

    # If the result is just '[]' or empty, treat it as unparseable
    if s == '[]' or s == '':
        return None
        
    return s


# --- 2. Main Loading and Population Function ---

def load_and_populate_chroma(
    csv_path: str, 
    collection_name: str = "my_document_embeddings",
    persist_directory: str = "my_vector_db"
) -> chromadb.Collection:
    
    print(f"Starting the process for file: {csv_path}")

    # Load the data, using 'sep=None' and 'engine='python'' for flexible reading
    try:
        df = pd.read_csv(csv_path, sep=None, engine='python')
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Map confirmed columns
    required_cols = ['text', 'embedding']
    if not all(col in df.columns for col in required_cols):
        # Fallback if column names were mangled by flexible separator
        if df.shape[1] >= 2:
            print("Warning: Column names were assumed to be 'text' and 'embedding'.")
            df.columns = required_cols
        else:
            print("Error: Could not find 'text' and 'embedding' columns.")
            return None

    # Apply fixes
    print("Cleaning embedding strings...")
    df['embedding'] = df['embedding'].apply(clean_embedding_string)

    print("Evaluating strings to list of floats...")
    # Apply literal_eval and handle potential errors by coercing to None
    df['embedding'] = df['embedding'].apply(lambda x: literal_eval(x) if x is not None else None)

    # --- FINAL DATA VALIDATION (Filters inconsistent dimensions) ---
    first_embedding = df['embedding'].dropna().iloc[0] if not df['embedding'].dropna().empty else None
    if first_embedding is None:
        print("Error: No valid embeddings found after cleaning.")
        return None
    
    expected_dim = len(first_embedding)
    print(f"Expected embedding dimension based on first entry: {expected_dim}")

    # Filter out rows where the embedding is None or has incorrect dimensions
    valid_mask = df['embedding'].apply(lambda x: x is not None and isinstance(x, list) and len(x) == expected_dim)
    df_valid = df[valid_mask].copy()
    
    if len(df) != len(df_valid):
        print(f"Warning: Dropped {len(df) - len(df_valid)} invalid rows.")
    
    if df_valid.empty:
        print("Error: All rows were filtered out.")
        return None

    # Connect to ChromaDB
    print(f"Initializing ChromaDB and saving to directory: ./{persist_directory}")
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(name=collection_name)
    
    # Prepare data for ChromaDB format
    documents = df_valid['text'].tolist()
    embeddings = df_valid['embedding'].tolist()
    ids = [str(x) for x in df_valid.index.tolist()] # Use index for IDs
    
    # Add data to the collection (without the optional 'metadatas' parameter)
    print(f"Adding {len(documents)} documents to the ChromaDB collection...")
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=ids
    )
    
    print(f"Successfully populated collection '{collection_name}' and saved to ./{persist_directory}.")
    return collection

# --- 3. Script Execution Block with File Dialog ---

if __name__ == "__main__":
    
    root = tk.Tk()
    root.withdraw() 
    
    print("A file selection window will now open. Please select your CSV file.")

    CSV_FILE_PATH = filedialog.askopenfilename(
        title="Select the Embedding CSV File",
        filetypes=[("CSV files", "*.csv")]
    )
    
    if CSV_FILE_PATH:
        # --- CONFIGURATION ---
        COLLECTION_NAME = 'my_document_embeddings'
        PERSIST_DIRECTORY = 'my_vector_db' 
        # ---------------------
        
        db_collection = load_and_populate_chroma(
            csv_path=CSV_FILE_PATH,
            collection_name=COLLECTION_NAME,
            persist_directory=PERSIST_DIRECTORY
        )
        
        if db_collection:
            print("\n--- Verification ---")
            print(f"Database saved to the '{PERSIST_DIRECTORY}' folder.")
            print(f"Total documents in collection: {db_collection.count()}")
    else:
        print("File selection cancelled. Exiting script.")
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from google import genai
from google.genai import types
from typing import List


EMBEDDING_MODEL = "gemini-embedding-001"

CHUNK_SIZE_WORDS = 200      
OVERLAP_WORDS = 50          
# ---------------------------------------------------------------------

try:
   
    client = genai.Client()

except Exception as e:
    print("ERROR: Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set.")
    print(f"Details: {e}")
    exit()

#-----------------------------------------------------------------------------------

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> List[str]:
    """
    Splits text into overlapping chunks based on word count.
    This logic mimics the implementation suggested in your shared PDF snippet. [cite: 47, 170]
    """
    cleaned_text = text.replace('\r', '').strip()
    
   
    words = cleaned_text.split()
    
    chunks = []
    start = 0 
    
   #-------------------------------------------------------------------------------------
    while start < len(words):
        
        end = start + chunk_size
        
       
        chunk = " ".join(words[start:end])
        chunks.append(chunk) # [cite: 175]
        
       
        start += (chunk_size - overlap)
        
    
    return [c for c in chunks if len(c) > 20]


def generate_embeddings_and_save_csv():
    """Main pipeline to read file, generate embeddings, and save to CSV."""
    
    print("A file selection window will now pop up. Please select your raw or enriched .txt file.")
    root = tk.Tk()
    root.withdraw() 
    
    input_file_path = filedialog.askopenfilename(
        title="Select the Text File to Embed",
        filetypes=[("Text files", "*.txt")]
    )

    if not input_file_path:
        print("No file selected. Exiting script.")
        return

    
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
        
    print(f"Document split into {len(text_chunks)} overlapping chunks (Size: {CHUNK_SIZE_WORDS} words, Overlap: {OVERLAP_WORDS} words).")
    
    
    print("--- Calling Gemini API to generate embeddings (This may take a moment) ---")
    
    try:
        
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text_chunks
        )
        
       
        embeddings_list = response.embeddings
        
    except Exception as e:
        print(f"\nAPI Error: An error occurred during the embedding call. {e}")
        print("Check your API key validity, internet connection, and usage limits.")
        return
        
    
   
    data = {
        'text': text_chunks,
        'embedding': embeddings_list
    }
    df = pd.DataFrame(data)
    

    base_name = os.path.basename(input_file_path).replace('.txt', '')
    output_file_name = f"{base_name}_embeddings.csv" 
    
    output_dir = os.path.dirname(input_file_path)
    output_file_path = os.path.join(output_dir, output_file_name)
    
    # Save the CSV file [cite: 373]
    df.to_csv(output_file_path, index=False)

    print("\n✅ Overlapping Embedding Generation Complete!")
    print(f"Output CSV saved to: {output_file_path}")
    print(f"Total entries: {len(df)}")


if __name__ == "__main__":
    generate_embeddings_and_save_csv()
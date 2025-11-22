import pandas as pd
from sentence_transformers import SentenceTransformer
import sys
import os

# --- Constants ---
CHUNK_SIZE = 450
OVERLAP = 50
# -----------------

def create_chunks(text_content, chunk_size, overlap):
    """
    Splits text into chunks of 'chunk_size' words, 
    with an overlap of 'overlap' words.
    """
    words = text_content.split()
    
    # Calculate step: If chunk is 450 and overlap is 50, we move 400 words at a time.
    step = chunk_size - overlap
    
    chunks = []
    
    # Iterate through the words using a sliding window
    for i in range(0, len(words), step):
        # Slice the list of words from i to i + chunk_size
        chunk_words = words[i : i + chunk_size]
        
        # Join back into a string
        chunk_text = " ".join(chunk_words)
        
        # Only add non-empty chunks
        if chunk_text:
            chunks.append(chunk_text)
            
    return chunks

def main():
    # 1. Check Command Line Arguments
    if len(sys.argv) < 2:
        print("❌ Error: Missing input file.")
        print("Usage: python embed_chunked.py <input_text_file>")
        return

    input_path = sys.argv[1]

    # 2. Verify Input File Exists
    if not os.path.exists(input_path):
        print(f"❌ Error: File not found at '{input_path}'")
        return

    # 3. Determine Output Filename
    base_name, _ = os.path.splitext(input_path)
    output_path = f"{base_name}_chunked_embeddings.csv"

    # 4. Load Model
    model_name = 'all-MiniLM-L6-v2'
    print(f"⏳ Loading model '{model_name}'...")
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # 5. Read File and Create Chunks
    print(f"📖 Reading from '{input_path}'...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            # Read the entire file content into one string
            full_text = f.read()
            
            # Optional: Replace newlines with spaces to treat the file as one continuous flow
            full_text = full_text.replace('\n', ' ')

        if not full_text.strip():
            print("❌ Error: Input file is empty.")
            return

        print("✂️  Chunking text...")
        text_chunks = create_chunks(full_text, CHUNK_SIZE, OVERLAP)
        
        print(f"🧩 Created {len(text_chunks)} chunks. Generating embeddings...")
        
        # 6. Generate Embeddings
        embeddings = model.encode(text_chunks, show_progress_bar=True)

        # 7. Save to CSV with explicit float conversion
        embedding_list = [[float(val) for val in emb] for emb in embeddings]
        
        df = pd.DataFrame({
            'chunk_id': range(len(text_chunks)), # Helpful to keep track of order
            'text_chunk': text_chunks,
            'embedding': embedding_list
        })

        df.to_csv(output_path, index=False, encoding='utf-8')

        print("-" * 40)
        print(f"✅ Success! Process complete.")
        print(f"📂 Input:  {input_path}")
        print(f"💾 Output: {output_path}")
        print(f"📊 Stats:  {len(text_chunks)} chunks created (Size: {CHUNK_SIZE}, Overlap: {OVERLAP})")
        print("-" * 40)

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
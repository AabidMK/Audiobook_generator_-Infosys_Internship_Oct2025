import os
import csv
import pandas as pd
from sentence_transformers import SentenceTransformer

class LocalTextEmbedder:
    def __init__(self, model_name='all-MiniLM-L6-v2', chunk_size=500, overlap=50):
        print(f"Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_into_chunks(self, text):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.overlap
        return chunks

    def process_file(self, extracted_text_file):
        """Process text file and generate embeddings"""
        if not os.path.exists(extracted_text_file):
            print(f"File not found: {extracted_text_file}")
            return

        # Read the text file
        with open(extracted_text_file, 'r', encoding='utf-8') as f:
            text_data = f.read().strip()

        if not text_data:
            print("No text found in the file.")
            return

        # Process text lines
        text_lines = [line.strip() for line in text_data.split("\n") if line.strip()]
        text_chunks = []
        
        for line in text_lines:
            if len(line) > self.chunk_size:
                text_chunks.extend(self._split_into_chunks(line))
            else:
                text_chunks.append(line)

        print(f"Generating embeddings for {len(text_chunks)} text chunks...")
        
        # Generate embeddings
        embeddings = self.model.encode(text_chunks)
        
        # Create DataFrame with embeddings
        df = pd.DataFrame({
            "Text": text_chunks,
            "Embedding": [",".join([f"{x:.6f}" for x in emb]) for emb in embeddings]
        })
        
        # Save to CSV
        output_file = os.path.splitext(extracted_text_file)[0] + "_embeddings_table.csv"
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
        
        # Print results
        print("\nEmbedding Table Preview:")
        print(df.head().to_string(index=False))
        print(f"\nEmbeddings table saved successfully to: {output_file}")
        
        return df

if __name__ == "__main__":
    print("\n==========================")
    print("LOCAL TEXT EMBEDDING GENERATOR")
    print("==========================\n")
    
    file_path = input("Enter path to extracted text file (e.g., Sample2_extracted_text.txt): ").strip()
    
    # Create embedder instance and process file
    embedder = LocalTextEmbedder()
    embedder.process_file(file_path)
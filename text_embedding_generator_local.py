import os
import csv
import pandas as pd
from sentence_transformers import SentenceTransformer

class LocalTextEmbedder:
    """
    Generates embeddings for extracted text using a local SentenceTransformer model.
    Splits text into limited-size chunks (default: 500 chars) and saves output as
    a clean 2-column table: Text | Embedding
    """
    def __init__(self, model_name='all-MiniLM-L6-v2', chunk_size=500):
        print(f" Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size

    def _split_into_chunks(self, text, chunk_size):
        """Split large text into smaller chunks (<= chunk_size characters)."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def process_file(self, extracted_text_file):
        if not os.path.exists(extracted_text_file):
            print(f" File not found: {extracted_text_file}")
            return

        with open(extracted_text_file, 'r', encoding='utf-8') as f:
            text_data = f.read().strip()

        if not text_data:
            print(" No text found in the file.")
            return

        
        text_lines = [line.strip() for line in text_data.split("\n") if line.strip()]
        text_chunks = []
        for line in text_lines:
            if len(line) > self.chunk_size:
                text_chunks.extend(self._split_into_chunks(line, self.chunk_size))
            else:
                text_chunks.append(line)

        print(f" Generating embeddings for {len(text_chunks)} text chunks...")

        embeddings = self.model.encode(text_chunks)

        df = pd.DataFrame({
            "Text": text_chunks,
            "Embedding": [", ".join([f"{x:.6f}" for x in emb]) for emb in embeddings]
        })

        output_file = os.path.splitext(extracted_text_file)[0] + "_embeddings_table.csv"
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')

        print("\n Embedding Table Preview:")
        print(df.head().to_string(index=False))
        print(f"\n Embeddings table saved successfully to: {output_file}")


if __name__ == "__main__":
    print("\n==============================")
    print("LOCAL TEXT EMBEDDING GENERATOR")
    print("==============================\n")

    file_path = input(" Enter path to extracted text file (e.g. Sample_2_extracted_text.txt): ").strip()
    embedder = LocalTextEmbedder(chunk_size=500)  # limit to 500 characters per chunk
    embedder.process_file(file_path)



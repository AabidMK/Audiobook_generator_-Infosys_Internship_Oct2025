import os
import csv
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Input text files → Output CSV files
files = {
    "sample1_extractedtext_output.txt": "sample1_embeddings_table.csv",
    "sample2_extractedtext_output.txt": "sample2_embeddings_table.csv",
    "sample3_extractedtext_output.txt": "sample3_embeddings_table.csv",
    "sample4_extractedtext_output.txt": "sample4_embeddings_table.csv",
}

print("\n🔍 Generating line-by-line embeddings...\n")

for input_file, output_csv in files.items():

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        continue

    print(f"📄 Processing: {input_file}")

    # Read all lines separately
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    # Generate embeddings line by line
    embeddings = model.encode(lines).tolist()

    # Save to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Text", "Embedding"])  # header row

        for text, emb in zip(lines, embeddings):
            writer.writerow([text, emb])

    print(f"✅ Saved table: {output_csv}\n")

print("🎉 Done! All embedding tables generated.")

import os
import csv
import nltk
import pandas as pd
from sentence_transformers import SentenceTransformer

# Download tokenizer
nltk.download('punkt', quiet=True)


def chunk_text_with_sentence_overlap(text, max_chunk_chars=700, overlap_sentences=2):
    """
    Creates chunks using full sentences with overlap.
    No words cut. No sentence cutoff.
    Overlap ensures smooth audiobook context.
    """
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sent_len = len(sentence)

        # If adding this sentence exceeds chunk limit → finalize current chunk
        if current_length + sent_len > max_chunk_chars:
            chunks.append(" ".join(current_chunk))

            # Apply overlap: keep last few sentences
            current_chunk = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []

            current_length = sum(len(s) for s in current_chunk)

        # Add next sentence
        current_chunk.append(sentence)
        current_length += sent_len

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def generate_embeddings(input_file, max_chunk_chars=700, overlap_sentences=2, model_name="all-MiniLM-L6-v2"):
    """
    Generates embeddings for clean audiobook-safe text chunks.
    """
    if not os.path.exists(input_file):
        print("❌ File not found")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("❌ Empty file")
        return

    print("\n📌 Splitting text (sentences + overlap)...")
    chunks = chunk_text_with_sentence_overlap(
        text,
        max_chunk_chars=max_chunk_chars,
        overlap_sentences=overlap_sentences
    )

    print(f"✅ Total chunks created: {len(chunks)}")

    print("\n📌 Loading embedding model...")
    model = SentenceTransformer(model_name)

    print("\n📌 Generating embeddings...")
    embeddings = model.encode(chunks, show_progress_bar=True)

    df = pd.DataFrame({
        "Text": chunks,
        "Embedding": [", ".join([f"{v:.6f}" for v in e]) for e in embeddings]
    })

    output_file = os.path.splitext(input_file)[0] + "_embeddings.csv"
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL)

    print(f"\n✅ CSV saved to: {output_file}")
    print("\nSample Output:")
    print(df.head())

    return output_file


# ---------------- MAIN RUNNER ----------------
if __name__ == "__main__":
    print("\n==============================")
    print(" AI AUDIOBOOK — EMBEDDING GENERATOR")
    print("==============================\n")

    input_file = input("Enter extracted text file path: ").strip()
    max_chunk_chars = int(input("Max chunk size (recommended 700): ").strip() or 700)
    overlap_sentences = int(input("Overlap sentences (recommended 1–3): ").strip() or 2)

    generate_embeddings(
        input_file,
        max_chunk_chars=max_chunk_chars,
        overlap_sentences=overlap_sentences
    )

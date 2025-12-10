import os
import csv
import textwrap
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY not set in environment!")

genai.configure(api_key=api_key)

# Gemini Embedding Model
EMBED_MODEL = "models/text-embedding-004"   # Best one


# -----------------------------
# Helper: chunk text
# -----------------------------
def chunk_text(text: str, chunk_size: int = 800) -> list:
    """
    Chunk text into smaller parts so embeddings are stable.
    """
    return textwrap.wrap(text, chunk_size)


# -----------------------------
# Generate embeddings
# -----------------------------
def generate_embeddings(text_list):
    """
    Accepts list of text chunks.
    Returns list of embedding vectors.
    """
    logging.info(f"🔍 Generating embeddings for {len(text_list)} chunks...")

    embeddings = []
    for i, chunk in enumerate(text_list, 1):
        try:
            response = genai.embed_content(
                model=EMBED_MODEL,
                content=chunk,
            )
            vector = response["embedding"]
            embeddings.append((chunk, vector))
            logging.info(f"✅ Chunk {i} embedded ({len(vector)} dims)")
        except Exception as e:
            logging.error(f"❌ Failed to embed chunk {i}: {e}")

    return embeddings


# -----------------------------
# Save CSV
# -----------------------------
def save_embeddings_to_csv(embeddings, output_csv="embeddings.csv"):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "embedding"])

        for text_chunk, vector in embeddings:
            writer.writerow([text_chunk, vector])

    logging.info(f"📁 Embeddings saved to: {output_csv}")


# -----------------------------
# Main process
# -----------------------------
def main():
    input_file = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\extracted_output.txt"

    # Read extracted text
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        logging.error("❌ extracted_output.txt is empty!")
        return

    logging.info("📘 Text loaded successfully. Splitting into chunks...")
    chunks = chunk_text(text, chunk_size=800)

    # Create embeddings
    embeddings = generate_embeddings(chunks)

    # Save CSV
    save_embeddings_to_csv(embeddings, output_csv="text_embeddings.csv")

    logging.info("🎉 Embedding generation complete!")


if __name__ == "__main__":
    main()
import csv
import ast
import chromadb
from chromadb.config import Settings
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---------------------------------------------------
# Load Embeddings CSV
# ---------------------------------------------------
def load_embeddings(csv_path):
    texts = []
    embeddings = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            embeddings.append(ast.literal_eval(row["embedding"]))  # Convert string → list

    return texts, embeddings


# ---------------------------------------------------
# Store in ChromaDB
# ---------------------------------------------------
def store_in_chroma(texts, embeddings, collection_name="audiobook_embeddings"):
    # Create Chroma persistent DB in ./chroma_db
    client = chromadb.PersistentClient(path="chroma_db")

    # Create collection or get if exists
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # cosine similarity recommended for embeddings
    )

    logging.info(f"📦 Storing {len(texts)} embeddings in ChromaDB...")

    ids = [f"chunk_{i}" for i in range(len(texts))]
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings
    )

    logging.info("✅ Embeddings successfully stored in ChromaDB!")
    return collection


# ---------------------------------------------------
# Test Similarity Search
# ---------------------------------------------------
def test_query(collection):
    query = input("\n🔎 Enter a search query: ")

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    print("\n📌 Top Matches:")
    for doc, score in zip(results["documents"][0], results["distances"][0]):
        print(f"→ Score: {score:.4f}")
        print(f"  {doc[:200]} ...\n")


# ---------------------------------------------------
# Main run
# ---------------------------------------------------
if __name__ == "__main__":
    CSV_PATH = "text_embeddings.csv"

    logging.info("📥 Loading CSV embeddings...")
    texts, embeddings = load_embeddings(CSV_PATH)

    logging.info("🧠 Initializing ChromaDB...")
    collection = store_in_chroma(texts, embeddings)

    logging.info("🧪 Testing vector search...")
    test_query(collection)

    logging.info("🎉 ChromaDB pipeline complete!")
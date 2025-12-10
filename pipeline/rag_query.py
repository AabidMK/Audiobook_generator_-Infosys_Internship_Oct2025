import logging
import os
import google.generativeai as genai
import chromadb
from chromadb.config import Settings
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -----------------------------
# Gemini Embedding Model
# -----------------------------
EMB_MODEL = "text-embedding-004"

def get_query_embedding(query: str):
    """Convert user query to an embedding vector."""
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    result = genai.embed_content(
        model=EMB_MODEL,
        content=query,
        task_type="retrieval_query"
    )

    return result["embedding"]


# -----------------------------
# Load ChromaDB Collection
# -----------------------------
def load_chroma_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    return client.get_collection(name="document_embeddings")


# -----------------------------
# RAG - Retrieve relevant chunks
# -----------------------------
def retrieve_top_k(query_embedding, collection, k=5):
    """Returns top-k similar text chunks."""

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    return results


# -----------------------------
# LLM - Answer generation
# -----------------------------
def generate_answer(query, retrieved_chunks):
    """Use Gemini to answer based on retrieved context."""
    
    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
You are a helpful AI assistant. Use ONLY the following context to answer the question.

CONTEXT:
{context}

QUESTION:
{query}

Provide a clear, well-structured answer. Do NOT hallucinate.
"""

    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2}
    )

    return response.text


# -----------------------------
# MAIN QUERY PIPELINE
# -----------------------------
if __name__ == "__main__":
    query = input("\n🔎 Enter your query: ")

    logging.info("📥 Generating query embedding...")
    query_emb = get_query_embedding(query)

    logging.info("📁 Loading ChromaDB collection...")
    collection = load_chroma_collection()

    logging.info("🧠 Retrieving top-k most relevant chunks...")
    results = retrieve_top_k(query_emb, collection, k=5)

    documents = results["documents"][0]  # top-k chunks from DB

    logging.info("✍️ Generating final answer with Gemini...")
    answer = generate_answer(query, documents)

    print("\n==============================")
    print("📘 ANSWER:")
    print("==============================\n")
    print(answer)
    print("\n==============================\n")
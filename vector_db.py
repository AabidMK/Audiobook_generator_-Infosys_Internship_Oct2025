# vector_db.py

import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import Chroma

# Folder to store vector database
VECTOR_DB_DIR = "vector_db"

# Embedding Model (free local model)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Split text into chunks
def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    return splitter.split_text(text)

# Save text into Chroma DB
def save_to_vector_db(text: str, doc_id: str):
    chunks = chunk_text(text)
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

    vectors = embedding_model.encode(chunks).tolist()
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=None,
    )

    db.add_texts(
        texts=chunks,
        ids=ids,
        embeddings=vectors
    )

    db.persist()
    return len(chunks)

# Search query in vector DB
def search_similar(query: str, k: int = 3):
    db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=None,
    )

    q_embed = embedding_model.encode([query]).tolist()
    results = db.similarity_search_by_vector(q_embed[0], k=k)
    return results

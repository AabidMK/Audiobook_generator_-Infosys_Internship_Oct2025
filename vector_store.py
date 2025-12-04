import os
import uuid
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Initialize ChromaDB client
client = chromadb.PersistentClient(
    path="vector_storage"
)

# Create / Load a collection
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Load Sentence Transformer model for embedding
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def store_document(doc_text: str):
    doc_id = str(uuid.uuid4())
    embedding = embedding_model.embed_query(doc_text)

    collection.add(
        ids=[doc_id],
        documents=[doc_text],
        embeddings=[embedding]
    )

    return doc_id


def query_document(query: str):
    embedding = embedding_model.embed_query(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    return results

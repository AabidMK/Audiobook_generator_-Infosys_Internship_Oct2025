# generate_embeddings.py
import os
import uuid
from typing import List, Dict, Optional, Union
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

# Configuration
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_store")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "pdf_embeddings")

# Initialize Chroma and embedding model (lazy init for faster imports)
_chroma_client = PersistentClient(path=CHROMA_DIR)
_collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)

_embed_model = None
def get_embed_model():
    """Lazily load SentenceTransformer model to avoid heavy startup cost."""
    global _embed_model
    if _embed_model is None:
        print(f"🔹 Loading embedding model: {EMBED_MODEL}")
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def embed_texts_and_store(
    chunks: List[str],
    metadata: Optional[Union[Dict, List[Dict]]] = None,
    prevent_duplicates: bool = True
) -> List[str]:
    """
    Embed and store chunks into ChromaDB.
    
    Args:
        chunks: List of text segments to embed.
        metadata: Optional dict or list of dicts for each chunk.
        prevent_duplicates: Avoid storing duplicate text chunks.
        
    Returns:
        List of inserted document IDs.
    """
    model = get_embed_model()
    ids, docs, embs, metas = [], [], [], []

    if metadata is None:
        metadata = [None] * len(chunks)
    elif isinstance(metadata, dict):
        metadata = [metadata] * len(chunks)

    for idx, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            continue

        # Optionally prevent duplicates
        if prevent_duplicates:
            existing = _collection.query(
                query_texts=[chunk],
                n_results=1,
                include=["documents"]
            )
            if existing and existing.get("documents") and chunk in existing["documents"][0]:
                continue

        uid = str(uuid.uuid4())
        ids.append(uid)
        docs.append(chunk)
        embs.append(model.encode(chunk).tolist())
        metas.append(metadata[idx] or {})

    if docs:
        _collection.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)

    return ids


def query_chroma_by_text(query_text: str, n_results: int = 3) -> Dict[str, List]:
    """
    Perform semantic similarity search in Chroma using raw query text.
    
    Args:
        query_text: The user query to search for.
        n_results: Number of top results to return.
    
    Returns:
        Dictionary with 'documents', 'metadatas', and 'distances'.
    """
    if not query_text.strip():
        return {"documents": [], "metadatas": [], "distances": []}

    res = _collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    if res and "documents" in res and res["documents"]:
        return {
            "documents": res["documents"][0],
            "metadatas": res.get("metadatas", [[]])[0],
            "distances": res.get("distances", [[]])[0],
        }

    return {"documents": [], "metadatas": [], "distances": []}

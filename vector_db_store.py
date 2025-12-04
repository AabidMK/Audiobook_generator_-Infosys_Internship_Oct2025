"""
Vector DB Store Module
Loads embedding CSV files and stores them into a Chroma vector database.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Optional, Sequence

import chromadb


class VectorDBStore:
    """Persist embeddings from CSV files into a Chroma vector database."""

    def __init__(
        self,
        persist_directory: str = "vector_store",
        collection_name: str = "audiobook_embeddings",
    ) -> None:
        """
        Args:
            persist_directory: Directory where the Chroma DB files will be stored.
            collection_name: Name of the Chroma collection.
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(collection_name)

    @staticmethod
    def _load_embeddings_from_csv(csv_path: Path) -> tuple[List[str], List[List[float]]]:
        """Load text chunks and embeddings from a CSV file."""
        texts: List[str] = []
        embeddings: List[List[float]] = []

        with csv_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if "text" not in reader.fieldnames or "embedding" not in reader.fieldnames:
                raise ValueError("CSV must contain 'text' and 'embedding' columns.")

            for row in reader:
                text = row["text"].strip()
                embedding_str = row["embedding"]
                embedding = json.loads(embedding_str)
                if not isinstance(embedding, list):
                    raise ValueError("Embedding must be a JSON array.")
                texts.append(text)
                embeddings.append([float(x) for x in embedding])

        if not texts:
            raise ValueError(f"No embeddings found in {csv_path}")

        return texts, embeddings

    def upsert_from_csv(
        self,
        csv_path: str,
        *,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Load embeddings from a CSV file and upsert them into the vector DB.

        Args:
            csv_path: Path to the embedding CSV file.
            metadata: Optional metadata dict to attach to every record.

        Returns:
            Dictionary containing counts of inserted vectors and the collection name.
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Embedding CSV not found: {csv_file}")

        texts, embeddings = self._load_embeddings_from_csv(csv_file)
        base_id = csv_file.stem

        ids = [f"{base_id}_{idx}" for idx in range(len(texts))]
        metadatas: Optional[List[dict]] = None
        if metadata:
            metadatas = [metadata.copy() for _ in ids]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return {
            "collection": self.collection.name,
            "vectors_added": len(ids),
            "csv_path": str(csv_file.resolve()),
            "persist_directory": str(self.persist_directory.resolve()),
        }


def store_embeddings_in_vector_db(
    csv_path: str,
    *,
    persist_directory: str = "vector_store",
    collection_name: str = "audiobook_embeddings",
    metadata: Optional[dict] = None,
) -> dict:
    """
    Convenience function to store embeddings from a CSV into Chroma DB.
    """
    store = VectorDBStore(
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    return store.upsert_from_csv(csv_path, metadata=metadata)


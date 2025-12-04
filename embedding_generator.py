"""
Embedding Generator Module
Generates text embeddings from extracted text files and saves them to CSV.
Uses sentence-transformers (free, open-source) for embedding generation.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """Generate embeddings for text extracted from documents."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        output_folder: str = "embeddings",
        max_words_per_chunk: int = 200,
    ) -> None:
        """
        Initialize the embedding generator.

        Args:
            model_name: Hugging Face sentence-transformers model name.
            output_folder: Directory where embedding CSV files will be saved.
            max_words_per_chunk: Maximum number of words per chunk when splitting text.
        """
        self.model_name = model_name
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.max_words_per_chunk = max_words_per_chunk

        # Lazy-load model to reduce startup time; load in __init__ for simplicity.
        self.model = SentenceTransformer(self.model_name)

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks of roughly max_words_per_chunk words.

        Uses sentence boundaries when possible to keep chunks coherent.
        """
        text = text.strip()
        if not text:
            return []

        # Split by sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            word_count = len(sentence.split())

            # If adding the sentence exceeds the limit, start a new chunk
            if current_chunk and current_word_count + word_count > self.max_words_per_chunk:
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = [sentence]
                current_word_count = word_count
            else:
                current_chunk.append(sentence)
                current_word_count += word_count

        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

        return chunks

    def _generate_embeddings(self, texts: Sequence[str]) -> List[List[float]]:
        """Generate embeddings for a sequence of text chunks."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, batch_size=16, show_progress_bar=False)
        return embeddings.tolist()

    def _save_as_csv(
        self,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        output_path: Path,
    ) -> None:
        """Save text and embeddings to a CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["text", "embedding"])
            for text, embedding in zip(texts, embeddings):
                writer.writerow([text, json.dumps(embedding)])

    def generate_embeddings_from_text(self, text: str) -> List[List[float]]:
        """Generate embeddings directly from a text string."""
        chunks = self._split_text_into_chunks(text)
        embeddings = self._generate_embeddings(chunks)
        return embeddings

    def process_text(
        self, text: str, output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate embeddings for the provided text and save to CSV.

        Args:
            text: Input text string.
            output_filename: Optional output filename for the CSV.

        Returns:
            Path to the generated CSV file.
        """
        chunks = self._split_text_into_chunks(text)
        embeddings = self._generate_embeddings(chunks)

        if output_filename is None:
            output_filename = "text_embeddings.csv"

        output_path = self.output_folder / output_filename
        self._save_as_csv(chunks, embeddings, output_path)
        return output_path

    def process_file(
        self,
        text_file_path: str,
        output_filename: Optional[str] = None,
    ) -> Path:
        """
        Load text from file, generate embeddings, and save as CSV.

        Args:
            text_file_path: Path to the extracted text file.
            output_filename: Optional output filename (defaults to derived name).

        Returns:
            Path to the generated CSV file.
        """
        text_path = Path(text_file_path)
        if not text_path.exists():
            raise FileNotFoundError(f"Text file not found: {text_path}")

        text = text_path.read_text(encoding="utf-8")

        if output_filename is None:
            output_filename = text_path.stem.replace("_extracted", "").replace("_enriched", "") + "_embeddings.csv"

        return self.process_text(text, output_filename)


def generate_embeddings(
    source_path: str,
    *,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    output_folder: str = "embeddings",
    max_words_per_chunk: int = 200,
) -> Path:
    """
    Convenience function to generate embeddings for a text file.

    Args:
        source_path: Path to the text file (extracted or enriched text).
        model_name: Sentence-transformers model name.
        output_folder: Directory to store the embedding CSV.
        max_words_per_chunk: Maximum words per text chunk before embedding.

    Returns:
        Path to the generated CSV file.
    """
    generator = EmbeddingGenerator(
        model_name=model_name,
        output_folder=output_folder,
        max_words_per_chunk=max_words_per_chunk,
    )
    return generator.process_file(source_path)


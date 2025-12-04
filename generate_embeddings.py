"""
CLI script to generate embeddings for extracted or enriched text files.
Usage:
    python generate_embeddings.py <text_file_path> [--model MODEL_NAME] [--output OUTPUT_CSV]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from embedding_generator import EmbeddingGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate embeddings for a text file.")
    parser.add_argument(
        "text_file",
        type=str,
        help="Path to the extracted or enriched text file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence-transformers model name (default: all-MiniLM-L6-v2).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output CSV filename (defaults to <text_filename>_embeddings.csv).",
    )
    parser.add_argument(
        "--output-folder",
        type=str,
        default="embeddings",
        help="Directory to store embedding CSV files (default: embeddings).",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=200,
        help="Maximum words per text chunk before embedding (default: 200).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generator = EmbeddingGenerator(
        model_name=args.model,
        output_folder=args.output_folder,
        max_words_per_chunk=args.max_words,
    )

    output_path = generator.process_file(args.text_file, output_filename=args.output)

    print("=" * 50)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 50)
    print(f"Input text file:  {Path(args.text_file).resolve()}")
    print(f"Embedding CSV:    {output_path.resolve()}")
    print(f"Model used:       {args.model}")
    print(f"Chunks created:   {len(output_path.read_text(encoding='utf-8').splitlines()) - 1}")


if __name__ == "__main__":
    main()


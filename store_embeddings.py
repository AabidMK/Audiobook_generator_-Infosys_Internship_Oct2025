# "\"\"
# CLI helper to load embedding CSVs and store them in a Chroma vector DB.
# Usage:
#     python store_embeddings.py embeddings/your_file_embeddings.csv \\
#         --persist-dir vector_store --collection audiobook_embeddings
# "\"\"

from __future__ import annotations

import argparse
from pathlib import Path

from vector_db_store import store_embeddings_in_vector_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Store embedding CSV into Chroma DB.")
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to the embedding CSV file.",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default="vector_store",
        help="Directory to persist the Chroma database (default: vector_store).",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="audiobook_embeddings",
        help="Chroma collection name (default: audiobook_embeddings).",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional source label to store as metadata.",
    )
    parser.add_argument(
        "--tags",
        type=str,
        nargs="*",
        default=None,
        help="Optional tags to store as metadata (space-separated).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    metadata = {}
    if args.source:
        metadata["source"] = args.source
    if args.tags:
        metadata["tags"] = args.tags
    if not metadata:
        metadata = None

    result = store_embeddings_in_vector_db(
        args.csv_path,
        persist_directory=args.persist_dir,
        collection_name=args.collection,
        metadata=metadata,
    )

    print("=" * 50)
    print("VECTOR DB UPSERT COMPLETE")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()


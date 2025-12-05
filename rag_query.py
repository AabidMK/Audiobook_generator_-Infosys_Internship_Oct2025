"""
RAG (Retrieval-Augmented Generation) query pipeline

Given a user query:
- Retrieve top-k most similar chunks from ChromaDB
- Compose a grounded prompt with those chunks as context
- Call an LLM (Gemini or OpenAI) to produce the final answer

CLI usage examples:

  python rag_query.py --query "What is the objective of the audiobook generator?" --top-k 5
  python rag_query.py --query "Summarize the milestones" --provider gemini --top-k 3 --show-sources

Environment variables:
- GOOGLE_API_KEY (preferred) or GEMINI_API_KEY for Gemini
- OPENAI_API_KEY for OpenAI (optional fallback)
"""

from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for LLM providers
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except Exception:
    genai = None
    HAS_GEMINI = False

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore


# ChromaDB
try:
    import chromadb
    HAS_CHROMA = True
except Exception:
    chromadb = None
    HAS_CHROMA = False


Provider = Literal["auto", "gemini", "openai"]


def _gemini_client(model_name: str = "gemini-2.5-flash"):
    if not HAS_GEMINI:
        return None
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        logger.error(f"Failed to init Gemini: {e}")
        return None


def _openai_client():
    if OpenAI is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to init OpenAI: {e}")
        return None


def get_collection(collection_name: str = "audiobook_embeddings", db_dir: str = "./vectordb"):
    if not HAS_CHROMA:
        raise RuntimeError("chromadb not installed. pip install chromadb")
    client = chromadb.PersistentClient(path=db_dir)
    return client.get_collection(name=collection_name)


@dataclass
class RetrievedChunk:
    text: str
    distance: float
    metadata: Dict[str, Any]


def retrieve_top_k(
    query: str,
    top_k: int = 5,
    collection_name: str = "audiobook_embeddings",
    db_dir: str = "./vectordb",
) -> List[RetrievedChunk]:
    """Retrieve top-k similar chunks from ChromaDB using query text.

    Relies on Chroma's internal ONNX embedder for the query (matches 384-dim).
    """
    col = get_collection(collection_name, db_dir)
    res = col.query(query_texts=[query], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    dists = res.get("distances", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    out: List[RetrievedChunk] = []
    for t, d, m in zip(docs, dists, metas):
        out.append(RetrievedChunk(text=t, distance=float(d), metadata=m or {}))
    return out


def build_context(chunks: List[RetrievedChunk]) -> str:
    parts = []
    for i, ch in enumerate(chunks, 1):
        src = ch.metadata.get("source", "unknown")
        idx = ch.metadata.get("index", i)
        parts.append(f"[Chunk {i} | src={src} | idx={idx} | dist={ch.distance:.3f}]\n{ch.text}")
    return "\n\n".join(parts)


SYSTEM_PROMPT = (
    "You are a precise assistant answering user questions using ONLY the provided context. "
    "If the answer is not in the context, say you don't know based on the document. "
    "Be concise, accurate, and avoid speculation. Rephrase naturally."
)


def answer_with_llm(
    query: str,
    context: str,
    provider: Provider = "auto",
    openai_model: str = "gpt-4o-mini",
    gemini_model: str = "gemini-2.5-flash",
    temperature: float = 0.2,
) -> str:
    """Generate an answer grounded on context using the chosen LLM provider."""

    # Auto selection preference: Gemini then OpenAI
    if provider == "auto":
        if HAS_GEMINI and (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
            provider = "gemini"
        elif OpenAI and os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            # No LLM available: return a fallback synthesized response
            return _fallback_answer(query, context)

    user_prompt = textwrap.dedent(f"""
    Question:
    {query}

    Context:
    {context}

    Instructions:
    - Answer using only the context above.
    - If not present in context, say you don't know based on the document.
    - Keep it concise and helpful.
    """)

    if provider == "gemini":
        client = _gemini_client(gemini_model)
        if not client:
            return _fallback_answer(query, context)
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
            resp = client.generate_content(full_prompt)
            return (getattr(resp, "text", None) or "").strip() or _fallback_answer(query, context)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return _fallback_answer(query, context)

    if provider == "openai":
        client = _openai_client()
        if not client:
            return _fallback_answer(query, context)
        try:
            chat = client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return (chat.choices[0].message.content or "").strip() or _fallback_answer(query, context)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return _fallback_answer(query, context)

    # Unknown provider
    return _fallback_answer(query, context)


def _fallback_answer(query: str, context: str) -> str:
    # Minimal non-LLM fallback: echo key info
    preview = context[:700]
    return (
        "No LLM available. Showing top retrieved context preview:\n\n" + preview
        + ("..." if len(context) > len(preview) else "")
    )


def rag_answer(
    query: str,
    top_k: int = 5,
    collection_name: str = "audiobook_embeddings",
    db_dir: str = "./vectordb",
    provider: Provider = "auto",
    show_sources: bool = False,
) -> Tuple[str, List[RetrievedChunk]]:
    """Full RAG pipeline: retrieve chunks then call LLM for final answer."""
    chunks = retrieve_top_k(query, top_k=top_k, collection_name=collection_name, db_dir=db_dir)
    context = build_context(chunks)
    answer = answer_with_llm(query, context, provider=provider)
    if show_sources:
        src_lines = [f"- source={c.metadata.get('source','?')} idx={c.metadata.get('index','?')} dist={c.distance:.3f}" for c in chunks]
        answer = answer + "\n\nSources:\n" + "\n".join(src_lines)
    return answer, chunks


def main():
    import argparse
    p = argparse.ArgumentParser(description="RAG query against ChromaDB and LLM answer")
    p.add_argument("--query", required=True, help="User query text")
    p.add_argument("--top-k", type=int, default=5, help="Top K chunks to retrieve")
    p.add_argument("--collection", default="audiobook_embeddings", help="Chroma collection name")
    p.add_argument("--db-dir", default="./vectordb", help="Chroma persistence directory")
    p.add_argument("--provider", choices=["auto", "gemini", "openai"], default="auto", help="LLM provider")
    p.add_argument("--show-sources", action="store_true", help="Append source metadata to the answer")
    args = p.parse_args()

    try:
        answer, chunks = rag_answer(
            query=args.query,
            top_k=args.top_k,
            collection_name=args.collection,
            db_dir=args.db_dir,
            provider=args.provider,
            show_sources=args.show_sources,
        )
        print("\n=== Answer ===\n" + answer)
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise


if __name__ == "__main__":
    main()

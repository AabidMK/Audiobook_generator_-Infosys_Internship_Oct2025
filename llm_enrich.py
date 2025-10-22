from __future__ import annotations

import os
from typing import Optional

from utils import chunk_text

# Optional OpenAI import; fall back gracefully if not available or no key.
try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional
    OpenAI = None  # type: ignore


SYS_PROMPT = (
    "You are a helpful assistant. Improve clarity and fix obvious OCR errors "
    "without changing meaning. Keep the output concise but faithful."
)


def _openai_client() -> Optional["OpenAI"]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception:
        return None


def enrich_text(text: str, model: Optional[str] = None, max_chars: int = 4000) -> str:
    """Optionally enrich text via OpenAI. If no API key or errors, return input."""
    text = text or ""
    client = _openai_client()
    if client is None:
        return text

    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chunks = chunk_text(text, max_chars=max_chars)
    outputs = []
    for ch in chunks:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYS_PROMPT},
                    {"role": "user", "content": ch},
                ],
                temperature=0.2,
            )
            outputs.append(resp.choices[0].message.content or ch)
        except Exception:
            outputs.append(ch)
    return "\n".join(outputs)

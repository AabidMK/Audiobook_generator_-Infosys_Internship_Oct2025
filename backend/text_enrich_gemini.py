# text_enrich_gemini.py
import os
import time
import math
from typing import List
from dotenv import load_dotenv

# Load environment variables if present
load_dotenv()

# === Config ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CHUNK_SIZE = int(os.getenv("ENRICH_CHUNK_SIZE", 12000))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", 1.5))
SLEEP_ON_RATE_LIMIT = float(os.getenv("SLEEP_ON_RATE_LIMIT", 5))

if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not set. Please export it or use a .env file.")

import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are an expert audiobook narrator.
Your task is to transform the extracted text into listener-friendly, audiobook-ready narration without leaving out any details.

Guidelines:
- Do NOT summarize or shorten the content.
- Retain all important facts and ideas from the original.
- Begin with a warm greeting such as: "Hello listeners, welcome..."
- Give a short overview of what the listener will learn before starting the main content.
- Make it conversational and engaging, not robotic.
- Rewrite sentences so they flow naturally when spoken aloud.
- Break down long sentences into shorter, clear phrases.
- Add natural pauses using "..." or line breaks for rhythm.
- Remove raw Markdown symbols (#, *, -, etc.) but preserve all information.
- Convert bullet points into spoken language (e.g., "First..., then..., finally...").
- Expand abbreviations (for example, "e.g." becomes "for example", "etc." becomes "and so on").
- Maintain the same depth of information — just make it sound warm, natural, and easy to listen to.
"""

# ============================================================ #
# Core Functions
# ============================================================ #

def chunk_text_by_chars(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split long text into chunks, keeping paragraph boundaries when possible."""
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        # try not to break mid-paragraph
        if end < n:
            next_break = text.rfind("\n\n", start, end + 200)
            if next_break > start:
                end = next_break + 2
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


def _call_gemini(prompt: str, model: str = MODEL_NAME, max_retries: int = MAX_RETRIES) -> str:
    """Call Gemini with retry, exponential backoff, and rate-limit handling."""
    for attempt in range(max_retries):
        try:
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(prompt)
            text = getattr(response, "text", None)
            if text:
                return text.strip()
            if isinstance(response, dict) and "output" in response:
                return str(response["output"]).strip()
            return str(response).strip()

        except Exception as exc:
            msg = str(exc).lower()
            sleep_time = (BACKOFF_FACTOR ** attempt)
            if "rate" in msg or "quota" in msg or "429" in msg:
                print(f"⚠️ Rate limit hit. Sleeping {SLEEP_ON_RATE_LIMIT}s before retry...")
                time.sleep(SLEEP_ON_RATE_LIMIT)
            else:
                print(f"⚠️ Error on attempt {attempt + 1}: {exc}. Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
    raise RuntimeError("❌ Failed to call Gemini after multiple retries.")


def enrich_text_with_gemini(text: str) -> str:
    """
    Enrich text into audiobook-style narration using Gemini.
    Handles long documents by chunking and concatenating results.
    Ensures the full content is preserved (no summarization).
    """
    if not text:
        return ""

    chunks = chunk_text_by_chars(text, CHUNK_SIZE)
    enriched_parts = []

    print(f"🔹 Processing {len(chunks)} chunk(s)...")

    for idx, chunk in enumerate(chunks, start=1):
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Chunk {idx} of {len(chunks)}:\n"
            f"Please transform this text into audiobook-friendly narration. "
            f"Do NOT summarize or omit details.\n\n"
            f"{chunk}\n\n"
            f"---\nReturn only the rewritten narration for this chunk."
        )
        try:
            resp_text = _call_gemini(prompt, model=MODEL_NAME)
            print(f"✅ Chunk {idx} processed successfully.")
        except Exception as e:
            print(f"⚠️ Gemini failed on chunk {idx}: {e}")
            resp_text = chunk  # fallback to raw text
        enriched_parts.append(resp_text)

    combined = "\n\n".join(enriched_parts)

    # Optional post-processing: Ensure only one greeting at start
    # e.g., Remove “Hello listeners” repeats from chunk boundaries
    combined = _normalize_greeting_repeats(combined)

    return combined


def _normalize_greeting_repeats(text: str) -> str:
    """Ensure greeting/intro appears only once."""
    lines = text.splitlines()
    cleaned = []
    first_greeting_found = False
    for line in lines:
        if not first_greeting_found and "hello" in line.lower():
            first_greeting_found = True
            cleaned.append(line)
        elif first_greeting_found and "hello" in line.lower():
            continue
        else:
            cleaned.append(line)
    return "\n".join(cleaned)

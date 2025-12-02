# backend/text_enrich.py
"""
Wrapper enrichment module used by app.py.

Behavior:
- If GEMINI_API_KEY is set and text_enrich_gemini is importable,
  uses enrich_text_with_gemini(text) for narration-ready transformation.
- Otherwise, falls back to a simple local enrichment.
- Provides enrich_text(text, use_gemini=False) entrypoint for app.py.
"""

import os
import traceback
from typing import Optional

def _simple_enrich(text: str) -> str:
    """Local fallback enrichment — cleans whitespace and adds narration prefix."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = "\n\n".join(lines)
    return "🎧 Narration-ready text:\n\n" + joined


# ===================================================== #
# Gemini Integration Detection
# ===================================================== #

_gemini_available = False
_text_enrich_gemini = None

try:
    try:
        # Try relative import for packaged execution
        from backend import text_enrich_gemini as _teg
    except ImportError:
        # Fallback for local direct run
        import text_enrich_gemini as _teg

    if hasattr(_teg, "enrich_text_with_gemini"):
        _text_enrich_gemini = _teg
        _gemini_available = True
        print("✅ Gemini enrichment module available.")
except Exception as e:
    print("⚠️ Gemini enrichment module not loaded:", e)
    _gemini_available = False
    _text_enrich_gemini = None


# ===================================================== #
# Canonical Entry Function
# ===================================================== #

def enrich_text(text: str, use_gemini: Optional[bool] = False) -> str:
    """
    Canonical enrichment interface.

    Args:
        text (str): Raw extracted text.
        use_gemini (bool, optional): Force use of Gemini API even if not auto-detected.

    Returns:
        str: Enriched narration-ready text.
    """
    if not text:
        return ""

    gemini_key = os.getenv("GEMINI_API_KEY")
    force_local = os.getenv("FORCE_LOCAL_ENRICH", "false").lower() in ("true", "1", "yes")
    want_gemini = (use_gemini or (gemini_key and not force_local)) and _gemini_available

    if want_gemini:
        try:
            print("🎙️ Using Gemini for text enrichment...")
            return _text_enrich_gemini.enrich_text_with_gemini(text)
        except Exception as e:
            print("⚠️ Gemini enrichment failed — falling back to local enrich.")
            traceback.print_exc()
            return _simple_enrich(text)

    print("📝 Using local enrichment only.")
    return _simple_enrich(text)

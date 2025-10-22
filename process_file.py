from __future__ import annotations

import argparse
from pathlib import Path

from utils import ensure_dirs, OUTPUT_TEXT_DIR, OUTPUT_AUDIO_DIR, file_stem
from extractor import extract_and_save
from llm_enrich import enrich_text
from tts import tts_synthesize


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text (and optional enrich/TTS) from a file to outputs/")
    parser.add_argument("path", help="Path to input file (.txt, .pdf, .docx, image)")
    parser.add_argument("--enrich", action="store_true", help="Enrich text with OpenAI if OPENAI_API_KEY is set")
    parser.add_argument("--tts", choices=["pyttsx3", "gtts"], help="Generate speech with selected engine")
    parser.add_argument("--rate", type=int, default=180, help="pyttsx3 rate (wpm)")
    parser.add_argument("--lang", default="en", help="gTTS language (default: en)")

    args = parser.parse_args()
    ensure_dirs()
    in_path = Path(args.path)
    if not in_path.exists():
        print(f"Input not found: {in_path}")
        return 2

    # Extract and save text
    txt_path = extract_and_save(in_path)
    text = txt_path.read_text(encoding="utf-8")
    print(f"Extracted text saved to: {txt_path}")

    # Optional enrich
    if args.enrich and text.strip():
        enriched = enrich_text(text)
        # Overwrite or save alongside
        txt_path.write_text(enriched, encoding="utf-8")
        print(f"Enriched text updated: {txt_path}")

    # Optional TTS
    if args.tts and text.strip():
        audio_path = tts_synthesize(
            text if not args.enrich else txt_path.read_text(encoding="utf-8"),
            engine=args.tts,
            rate=args.rate if args.tts == "pyttsx3" else None,
            language=args.lang if args.tts == "gtts" else "en",
            basename=file_stem(in_path)
        )
        print(f"Audio saved to: {audio_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
import argparse
from pathlib import Path
from typing import Optional

import google.generativeai as genai

AUDIOBOOK_SYSTEM_PROMPT = """You are an expert audiobook narrator.

Your task is to transform the provided source text into listener-friendly, audiobook-ready narration.
Follow these rules strictly:

1. Do NOT summarize or shorten the content. Keep all important details and explanations from the original text.
2. Begin with a warm greeting such as: "Hello listeners, welcome...".
3. After the greeting, provide a short spoken overview of what the listener will learn or experience.
4. Make the narration engaging and conversational, not just a direct copy of the text.
5. Rewrite the text so it flows naturally when spoken aloud.
6. Break down long or complex sentences into clear, shorter sentences.
7. Add natural pauses using "..." or line breaks to create rhythm and engagement.
8. Remove raw Markdown symbols such as #, *, -, and similar formatting characters, but preserve all of the information they represent.
9. Convert bullet points or lists into natural spoken form. For example: "First..., then..., finally...".
10. Expand abbreviations into spoken form. For example, say "for example" instead of "e.g.", and "and so on" instead of "etc.".
11. Maintain the same depth of information and level of detail as the original text.
12. Do not add new facts or change the meaning of the source material. You may only adjust style, tone, and structure to make it suitable for listening.
13. Write the final answer as continuous audiobook narration text only, without explanations about what you are doing.
"""


def configure_gemini(api_key: Optional[str] = None, model_name: str = "gemini-2.5-pro"):
    """Configure and return a Gemini GenerativeModel instance."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please set it in your environment before running this script."
        )

    genai.configure(api_key=key)
    return genai.GenerativeModel(model_name)


def enrich_text_with_gemini(source_text: str, model_name: str = "gemini-2.5-pro") -> str:
    """Send the source text to Gemini and return audiobook-style narration."""
    model = configure_gemini(model_name=model_name)

    # We send the system prompt plus the raw source text in a single request.
    prompt = (
        AUDIOBOOK_SYSTEM_PROMPT
        + "\n\n---\n\nHere is the source text that must be transformed into audiobook narration. "
        + "Remember: do NOT summarize or remove important details. Keep all information, just rewrite the style.\n\n"
        + source_text
    )

    response = model.generate_content(prompt)
    return response.text.strip()


def load_text(path: Path) -> str:
    """Load UTF-8 text from a file."""
    return path.read_text(encoding="utf-8")


def save_text(path: Path, text: str) -> None:
    """Save UTF-8 text to a file, creating parent folders if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Transform an extracted .txt file into audiobook-ready narration using Gemini API. "
            "The original text is treated as the source, and the enriched narration is saved to a new file."
        )
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the extracted source .txt file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="enriched_text",
        help="Directory where the enriched audiobook narration file will be saved (default: enriched_text)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="gemini-2.5-pro",
        help="Gemini model name to use (default: gemini-2.5-pro)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Prepare output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load source text directly from the input file (no extra copy)
    source_text = load_text(input_path)

    # Enrich text via Gemini
    enriched_text = enrich_text_with_gemini(source_text, model_name=args.model_name)

    # Save enriched output
    output_filename = input_path.stem + "_enriched.txt"
    output_path = output_dir / output_filename
    save_text(output_path, enriched_text)

    print(f"Enriched audiobook narration saved at: {output_path}")


if __name__ == "__main__":
    main()

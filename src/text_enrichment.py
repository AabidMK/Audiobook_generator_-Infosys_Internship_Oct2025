# MODULE 3 - Text Enrichment (Audiobook-style Narration)
"""
Uses Google Gemini API to rewrite extracted text into an engaging,
listener-friendly narration style.

Input  : extracted_output.txt
Output : enriched_output.txt
------------------------------------------------------"""

import logging
import os
from pathlib import Path
import textwrap
from google import genai
from dotenv import load_dotenv

load_dotenv()
print("Google Generative AI version:", genai.__version__)


# -------------------------
# Logging Setup
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class TextEnrichment:
    def __init__(self, model_name= "gemini-flash-latest"):
        """
        Initialize Gemini client with API key and model.
        Ensure GOOGLE_API_KEY is set as an environment variable.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ GOOGLE_API_KEY not found. Please set it using:\n"
                "   setx GOOGLE_API_KEY \"your_api_key_here\" (Windows)\n"
                "   or export GOOGLE_API_KEY=\"your_api_key_here\" (Mac/Linux)"
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def enrich_text(self, input_text: str) -> str:
        """
        Send text to Gemini and get audiobook-style rewritten version.
        """
        system_prompt = (
            "You are an audiobook narration expert. "
            "Rewrite the given text to make it engaging, listener-friendly, "
            "and natural for audiobook narration. "
            "Preserve factual meaning, but enhance tone, rhythm, and clarity "
            "to sound expressive when read aloud."
        )

        # Combine system prompt and user input into a single prompt
        full_prompt = f"{system_prompt}\n\nText to enrich:\n{input_text}"

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,  # Simple string format
                config={
                    "temperature": 0.7
                }
            )

            enriched_text = response.text.strip()
            logging.info("✅ Successfully received enriched text from Gemini.")
            return enriched_text
        except Exception as e:
            logging.error(f"❌ Gemini API call failed: {e}")
            return ""
        
    def chunk_text(self, text: str, max_chars: int = 2000):
        """
        Split text into smaller chunks to avoid model token limits.
        """
        return textwrap.wrap(text, max_chars)

    def process_file(self, input_path: str, output_path: str = "enriched_output.txt"):
        """
        Reads extracted text file, enriches it using Gemini, and saves output.
        Returns true if successful.
        """
        path = Path(input_path)
        if not path.exists():
            logging.error(f"Input file not found: {path}")
            return

        try:
            input_text = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            logging.warning("⚠️ Could not read with UTF-8, trying latin1...")
            input_text = path.read_text(encoding="latin1").strip()

        if not input_text:
            logging.warning("⚠️ Input file is empty. Nothing to enrich.")
            return False

        logging.info(f"Enriching text from '{path.name}' using Gemini API...")
        
        # Chunk text if it's very long
        chunks = self.chunk_text(input_text)
        enriched_chunks = []

        for i, chunk in enumerate(chunks, start=1):
            logging.info(f"Processing chunk {i}/{len(chunks)}...")
            enriched_chunk = self.enrich_text(chunk)
            if enriched_chunk:
                enriched_chunks.append(enriched_chunk)

        if enriched_chunks:
            enriched_text = "\n\n".join(enriched_chunks)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(enriched_text)
            logging.info(f"✅ Enriched text saved to {output_path}")
            return True
        else:
            logging.warning("⚠️ No enriched text returned from Gemini.")
            return False


# -------------------------
# Automatic Run
# -------------------------
if __name__ == "__main__":
    # Directly specify file path (no need for input)
    input_file = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\extracted_output.txt"
    output_file = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\enriched_output.txt"


    logging.info("🚀 Starting automatic Gemini text enrichment...")
    enricher = TextEnrichment(model_name="gemini-flash-latest")
    success = enricher.process_file(input_file, output_file)

    if success:
        logging.info("🎉 Text enrichment complete!")
    else:
        logging.error("❌ Text enrichment failed.")

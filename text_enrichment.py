import os
import sys
import requests
import json
from dotenv import load_dotenv

# ========================================
# Load Gemini API Key from .env file
# ========================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "❌ GEMINI_API_KEY not found in .env file. Please create a .env file with your key."
    )

# Gemini API Endpoint (updated to supported model)
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# System prompt to guide rewriting
SYSTEM_PROMPT = (
    "You are a professional language enhancer. Rewrite the given text in a more "
    "refined, grammatically correct, and engaging manner while preserving meaning."
)

# ========================================
# Core Functions
# ========================================

def read_text_file(file_path):
    """Read text content from a .txt file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_enriched_text(text, output_path):
    """Save the enriched text to a .txt file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Enriched text saved to '{output_path}'")


def enrich_text_with_gemini(text):
    """Send text to Google's Gemini API for rewriting."""
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{text}"}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Debug: check if response contains expected fields
        if "candidates" not in data or not data["candidates"]:
            print("⚠️ No valid candidates returned by Gemini.")
            print(json.dumps(data, indent=2))
            return None

        enriched_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return enriched_text

    except Exception as e:
        print(f"❌ Error enriching text with Gemini: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return None


def enrich_text(input_file):
    """Main enrichment function."""
    print(f"🔍 Reading text from: {input_file}")
    text = read_text_file(input_file)

    if not text:
        print("⚠️ No text found in the input file.")
        return None

    print("🧠 Sending text to Gemini for enrichment...")
    enriched_text = enrich_text_with_gemini(text)

    if enriched_text:
        output_file = os.path.splitext(input_file)[0] + "_enriched.txt"
        save_enriched_text(enriched_text, output_file)
        return output_file
    else:
        print("⚠️ No enriched text returned.")
        return None


# ========================================
# Command-line Entry
# ========================================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python text_enrichment.py <input_text_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    enrich_text(input_path)

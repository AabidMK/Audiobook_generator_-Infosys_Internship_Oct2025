import os
import sys
import requests
import json
from dotenv import load_dotenv


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "❌ GEMINI_API_KEY not found in .env file. Please create a .env file with your key."
    )


GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"



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
    """Send text to Google's Gemini API for audiobook narration rewriting."""
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

   
    prompt = f"""
You are an expert audiobook narrator.  

Your task is to transform the extracted text into listener-friendly audiobook-ready narration without leaving out details.  

Guidelines:

Do NOT summarize or cut down the content. Keep all important details from the original.  

Begin with a warm greeting such as: "Hello listeners, welcome...".

Provide a short summary of what the listener will learn before diving into the content.

Make it engaging and conversational, not just a direct copy.

Rewrite the text so it flows naturally when spoken aloud.  

Break down long or complex sentences into clear, shorter sentences.  

Add natural pauses using "..." or line breaks for rhythm and engagement.  

Remove raw Markdown symbols (like #, *, -, and so on), but keep all information they represent.  

Do NOT include any other special symbols in the final enriched text.

Rewrite bullet points or lists into spoken style. For example: "First..., then..., finally...".

Expand abbreviations (for example, "e.g." to "for example", "etc." to "and so on").  

Maintain the same depth of information, just make it more engaging, warm, and listener-friendly. 

Here is the extracted content:
{text}
"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

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

    print("🎧 Sending text to Gemini for audiobook narration enrichment...")
    enriched_text = enrich_text_with_gemini(text)

    if enriched_text:
        output_file = os.path.splitext(input_file)[0] + "_audiobook.txt"
        save_enriched_text(enriched_text, output_file)
        return output_file
    else:
        print("⚠️ No enriched text returned.")
        return None



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python text_enrichment.py <input_text_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    enrich_text(input_path)

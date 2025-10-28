import os
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = 'gemini-2.5-flash'

# Folder paths
INPUT_FOLDER = "output_files"
OUTPUT_FOLDER = "output_text_enrichment"
INPUT_SUFFIX = ".txt"
OUTPUT_SUFFIX = "_enriched.txt"


class TextEnricher:
    """
    Reads extracted text files, sends them to the Gemini API for rewriting,
    and saves the enriched output in a separate folder.
    """
    def __init__(self, api_key=None):
        try:
            if not api_key:
                raise ValueError("No API key provided.")
            self.client = genai.Client(api_key=api_key)
            print("Gemini client initialized successfully.")
        except Exception as e:
            raise EnvironmentError(f"Failed to initialize Gemini client. Error: {e}")

    def generate_system_prompt(self, target_style="professional, engaging, and audiobook-friendly"):
        """
        Generates the system prompt to guide the model's rewriting.
        """
        return (
            f"You are a skilled editor enhancing extracted raw text for audiobook narration. "
            f"Make it clear, fluent, and engaging while preserving the original meaning. "
            f"Do not add introductions or summaries. "
            f"The tone should be {target_style}."
        )

    def rewrite_text(self, raw_text, system_prompt):
        """
        Calls the Gemini API to rewrite the given text.
        """
        if not raw_text.strip():
            return "Content is empty, skipping enrichment."

        print(f"Sending {len(raw_text)} characters to Gemini...")

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=raw_text,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )
            return response.text.strip()
        except APIError as e:
            return f"API Error: {e}"
        except Exception as e:
            return f"Unexpected Error: {e}"

    def process_file(self, file_path):
        """
        Reads input text, rewrites it, and saves the output in the enrichment folder.
        """
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0].removesuffix(INPUT_SUFFIX.removesuffix('.txt'))
        output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}{OUTPUT_SUFFIX}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        except FileNotFoundError:
            print(f"Input file not found: {file_path}")
            return

        system_prompt = self.generate_system_prompt()
        enriched_text = self.rewrite_text(raw_text, system_prompt)

        if not enriched_text.startswith("Content is empty") and not enriched_text.startswith("API Error") and not enriched_text.startswith("Unexpected Error"):
            try:
                if not os.path.exists(OUTPUT_FOLDER):
                    os.makedirs(OUTPUT_FOLDER)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(enriched_text)
                print(f"Enriched text saved: {output_path}")
            except Exception as e:
                print(f"Error saving output file {output_path}: {e}")
        else:
            print(f"Skipped: {enriched_text}")


def process_all_files():
    """
    Processes all extracted text files in the output_files directory.
    """
    if not os.path.exists(INPUT_FOLDER):
        print(f"Folder '{INPUT_FOLDER}' not found.")
        return

    enricher = TextEnricher(api_key=API_KEY)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(INPUT_SUFFIX)]

    if not files:
        print(f"No files found ending with '{INPUT_SUFFIX}' in '{INPUT_FOLDER}'.")
        return

    print(f"--- Starting Text Enrichment for {len(files)} file(s) ---")

    for filename in files:
        file_path = os.path.join(INPUT_FOLDER, filename)
        print(f"\nProcessing: {filename}")
        enricher.process_file(file_path)

    print("\n--- Enrichment Complete ---")


if __name__ == "__main__":
    process_all_files()

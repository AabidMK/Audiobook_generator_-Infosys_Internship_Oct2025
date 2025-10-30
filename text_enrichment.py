import os
from google import genai
from google.genai.errors import APIError

MODEL_NAME = 'gemini-2.5-flash'

INPUT_SUFFIX = '_extracted_text.txt' 
OUTPUT_SUFFIX = '_enriched.txt'


class TextEnricher:
    """
    Reads extracted text, sends it to the Gemini API for rewriting, 
    and saves the enriched output.
    """
    def __init__(self, api_key=None):
        try:
            
            self.client = genai.Client(api_key=api_key)
            print(" Gemini client initialized.")
        except Exception as e:
            raise EnvironmentError(f"Failed to initialize Gemini client. Is GEMINI_API_KEY set? Error: {e}")

    def generate_system_prompt(self, target_style="professional, engaging, and suitable for an audiobook"):
        """
        Generates the system prompt to guide the LLM's rewriting task.
        """
        prompt = (
            f"You are a professional content editor tasked with enriching and rewriting raw, "
            f"extracted text. Your goal is to make the text more fluent, engaging, and polished. "
            f"Do not add any introductory or concluding remarks (e.g., 'Here is the rewritten text'). "
            f"Focus solely on rewriting the provided content. The rewritten style should be: "
            f"{target_style}."
        )
        return prompt

    def rewrite_text(self, raw_text, system_prompt):
        """
        Calls the Gemini API to rewrite the given raw text.
        """
        if not raw_text.strip():
            return "Content is empty, skipping enrichment."

        print(f"    -> Sending {len(raw_text)} characters to Gemini...")
        
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
            return f" API Error during enrichment: {e}"
        except Exception as e:
            return f" An unexpected error occurred: {e}"

    def process_file(self, input_file_path):
        """
        Full workflow: reads input, rewrites, and saves output.
        """
       
        base_name = os.path.splitext(input_file_path)[0].removesuffix(INPUT_SUFFIX.removesuffix('.txt'))
        output_file_path = f"{base_name}{OUTPUT_SUFFIX}"

        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        except FileNotFoundError:
            print(f"Input file not found: {input_file_path}")
            return

        system_prompt = self.generate_system_prompt()

        enriched_text = self.rewrite_text(raw_text, system_prompt)

        if not enriched_text.startswith(('Content is empty', '❌')):
            try:
                output_dir = os.path.dirname(output_file_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(enriched_text)
                print(f"Successfully saved enriched text to: {output_file_path}")
            except Exception as e:
                print(f" Error saving output file {output_file_path}: {e}")
        else:
            print(f"Skipped processing: {enriched_text}")


if __name__ == '__main__':

    extracted_files = [
        f"Sample 1{INPUT_SUFFIX}",
        f"Sample 2{INPUT_SUFFIX}",
        f"sample 3{INPUT_SUFFIX}",
        f"sample 4{INPUT_SUFFIX}"
       ,
    ]

    print("--- Starting Text Enrichment Module ---")
    
    try:
        enricher = TextEnricher()
        
        for file_name in extracted_files:
            print(f"\nProcessing: {file_name}")
            enricher.process_file(file_name)

    except EnvironmentError as e:
        print(f"\nCritical Error: {e}")
        print("Please set the GEMINI_API_KEY environment variable and ensure network connectivity.")

    print("\n--- Enrichment Complete ---")
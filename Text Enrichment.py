import os
import google.generativeai as genai

INPUT_DIR = "output"            
OUTPUT_DIR = "enriched_texts"   
GEMINI_API_KEY = "your_Api"
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are an advanced Text Analysis and Rephrasing Engine. Your task is to deeply comprehend the provided text and generate a rephrased version that strictly maintains the original meaning, intent, and factual information. You must adapt the text based on the user's explicit instructions for Target Audience, Tone, Length, or Specific Style/Focus. Do not introduce new facts or change the core message. The rephrased output must be a complete, standalone, and coherent piece of text.
"""
genai.configure(api_key=GEMINI_API_KEY)
def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()
def enrich_text_with_gemini(text: str) -> str:
    try:
        model=genai.GenerativeModel(MODEL_NAME)
        prompt=f"{SYSTEM_PROMPT}\n\nText:\n{text}"
        response=model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error enriching text: {e}")
        return text  
def process_file(file_path, output_dir):
    file_name = os.path.basename(file_path)
    print(f"\nProcessing: {file_name}")

    try:
        text=extract_text_from_txt(file_path)
        if not text:
            print(f"Skipping empty file: {file_name}")
            return

        enriched_text = enrich_text_with_gemini(text)

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, file_name.rsplit(".", 1)[0] + "_enriched.txt")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(enriched_text)

        print(f" Saved: {output_file}")

    except Exception as e:
        print(f" Failed processing {file_name}: {e}")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f" Input folder '{INPUT_DIR}' not found.")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".txt")]
    if not files:
        print(f"No .txt files found in '{INPUT_DIR}'.")
        return

    print(f"\nStarting enrichment pipeline using Gemini ({MODEL_NAME})...\n")
    for file_name in files:
        process_file(os.path.join(INPUT_DIR, file_name), OUTPUT_DIR)

    print("\nAll files enriched successfully!")
if __name__=="__main__":
    main()

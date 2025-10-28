import os
import google.generativeai as genai

<<<<<<< HEAD
INPUT_DIR = "output"
OUTPUT_DIR = "enriched_texts"
GEMINI_API_KEY = "AIzaSyBBP4wNii-Vf9R_MRJ3O_uOhUZtM1qMUQI"
=======
INPUT_DIR = "output"            
OUTPUT_DIR = "enriched_texts"   
GEMINI_API_KEY = "your_Api"
>>>>>>> 458c6381afc722d192173b4c1108c38241a7cd83
MODEL_NAME = "gemini-2.5-flash"

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

genai.configure(api_key=GEMINI_API_KEY)

def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def enrich_text_with_gemini(text: str) -> str:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"{SYSTEM_PROMPT}\n\nHere is the extracted content:\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error enriching text: {e}")
        return text

def process_file(file_path, output_dir):
    file_name = os.path.basename(file_path)
    print(f"\nProcessing: {file_name}")
    try:
        text = extract_text_from_txt(file_path)
        if not text:
            print(f"Skipping empty file: {file_name}")
            return
        enriched_text = enrich_text_with_gemini(text)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, file_name.rsplit(".", 1)[0] + "_narration.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(enriched_text)
        print(f"Saved: {output_file}")
    except Exception as e:
        print(f"Failed processing {file_name}: {e}")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Input folder '{INPUT_DIR}' not found.")
        return
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".txt")]
    if not files:
        print(f"No .txt files found in '{INPUT_DIR}'.")
        return
    print(f"\nStarting audiobook enrichment pipeline using Gemini ({MODEL_NAME})...\n")
    for file_name in files:
        process_file(os.path.join(INPUT_DIR, file_name), OUTPUT_DIR)
    print("\nAll files enriched and ready for narration!")

if __name__ == "__main__":
    main()

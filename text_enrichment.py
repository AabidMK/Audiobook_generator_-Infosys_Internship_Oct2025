# text_enrich_gemini.py
import os
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract

from google import genai  # correct import

API_KEY = "AIzaSyCYfjCBPKUItU3VSdc9x2uydhpZS-j--IQ"
client = genai.Client(api_key=API_KEY)

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                pt = page.extract_text()
                if pt:
                    text += pt + "\n"
        return text
    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext in [".png", ".jpg", ".jpeg"]:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def enrich_text(prompt_text, model_name="gemini-2.5-flash"):
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt_text
    )
    return resp.text

def main():
    files = input("Enter file paths separated by commas: ").split(",")
    all_text = ""
    for fp in files:
        fp = fp.strip()
        if os.path.exists(fp):
            print(f"Extracting from {fp}...")
            t = extract_text(fp)
            if t.strip():
                all_text += t + "\n\n"
        else:
            print("File not found:", fp)

    if not all_text.strip():
        print("No text to enrich — exiting.")
        return

    print("Calling Gemini API to enrich text...")
    enriched = enrich_text(all_text)
    print("=== Enriched Text ===")
    print(enriched)

    with open("enriched_output.txt", "w", encoding="utf-8") as f:
        f.write(enriched)
    print("Saved enriched text to enriched_output.txt")

if __name__ == "__main__":
    main()

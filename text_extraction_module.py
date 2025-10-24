import os
import io
import time
import fitz  
from docx import Document
from PIL import Image
import pytesseract
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_FOLDER="pdfs"
OUTPUT_FOLDER="output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_pdf(file_path, use_ocr=True):
    text=""
    with fitz.open(file_path) as pdf:
        for page_num, page in enumerate(pdf, start=1):
            page_text=page.get_text("text").strip()

            if use_ocr and not page_text:
                print(f" OCR needed on page {page_num} of {os.path.basename(file_path)}")
                try:
                    pix=page.get_pixmap(matrix=fitz.Matrix(1, 1))
                    img=Image.open(io.BytesIO(pix.tobytes("png")))

                    ocr_text=pytesseract.image_to_string(
                        img, lang="eng", config="--oem 1 --psm 6"
                    )
                    page_text=ocr_text.strip()
                except Exception as e:
                    print(f" OCR failed on {file_path} (page {page_num}): {e}")

            text+=page_text + "\n"
    return text.strip()


def extract_text_from_docx(file_path):
    try:
        doc=Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        print(f" Error reading DOCX {file_path}: {e}")
        return ""


def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""


def extract_text_from_file(file_path):
    ext=os.path.splitext(file_path)[1].lower()
    if ext==".pdf":
        return extract_text_from_pdf(file_path)
    elif ext==".docx":
        return extract_text_from_docx(file_path)
    elif ext==".txt":
        return extract_text_from_txt(file_path)
    else:
        print(f"Skipping unsupported file: {file_path}")
        return ""


def save_text(output_text, input_filename):
    base_name=os.path.splitext(os.path.basename(input_filename))[0]
    output_path=os.path.join(OUTPUT_FOLDER, f"{base_name}_extracted.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f" Saved output: {output_path}")
    except Exception as e:
        print(f" Error saving {input_filename}: {e}")


def process_file(filename):
    input_path=os.path.join(INPUT_FOLDER, filename)
    start=time.time()
    print(f"\nStarting: {filename}")
    try:
        text=extract_text_from_file(input_path)
        if text.strip():
            save_text(text, filename)
            elapsed=time.time() - start
            return f" Done {filename} ({elapsed:.1f}s)"
        else:
            return f"No text found in {filename}"
    except Exception as e:
        return f" Error in {filename}: {e}"


def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"Input folder '{INPUT_FOLDER}' not found.")
        return

    files=[f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    if not files:
        print(f"No PDF/DOCX/TXT files found in '{INPUT_FOLDER}'.")
        return

    print(f"Found {len(files)} file(s) in '{INPUT_FOLDER}'. Starting extraction...\n")

    max_workers=min(4, os.cpu_count() or 2)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures=[executor.submit(process_file, f) for f in files]
        for future in as_completed(futures):
            print(future.result())

    print("\n Extraction complete! Check the 'output' folder.")

if __name__=="__main__":
    main()

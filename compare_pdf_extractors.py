# MODULE 1 - Text Extraction (Compare PyPDF2 v/s pdfplumber)
"""------------------------------------------------------"""

import PyPDF2
import pdfplumber
from jiwer import wer, cer
import time

# STEP 1: Define file paths 
pdf_path = r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\AI AudioBook Generator.pdf"
"C:/Users/SWATI/OneDrive/Desktop/AIaudioBook/ground_truth.txt" == r"C:\Users\SWATI\OneDrive\Desktop\AIaudioBook\AI AudioBook Generator.pdf"

# STEP 2: Extraction functions 
def extract_text_pypdf2(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def extract_text_pdfplumber(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# STEP 3: Evaluation function
def evaluate_extraction(extracted_text, reference_text):
    word_error = wer(reference_text, extracted_text)
    char_error = cer(reference_text, extracted_text)
    return word_error, char_error

# STEP 4: Run extraction and evaluation
if __name__ == "__main__":
    # Load reference text
    with open("C:/Users/SWATI/OneDrive/Desktop/AIaudioBook/ground_truth.txt", "r", encoding="utf-8") as f:
        reference_text = f.read()

    print("🔍 Extracting text using PyPDF2...")
    start = time.time()
    text_pypdf2 = extract_text_pypdf2(pdf_path)
    pypdf2_time = time.time() - start
    print(f"✅ Done in {pypdf2_time:.2f} seconds.\n")

    print("🔍 Extracting text using pdfplumber...")
    start = time.time()
    text_pdfplumber = extract_text_pdfplumber(pdf_path)
    pdfplumber_time = time.time() - start
    print(f"✅ Done in {pdfplumber_time:.2f} seconds.\n")

    # Evaluate performance
    wer_pypdf2, cer_pypdf2 = evaluate_extraction(text_pypdf2, reference_text)
    wer_pdfplumber, cer_pdfplumber = evaluate_extraction(text_pdfplumber, reference_text)

    #  STEP 5: Display results
    print("📊 --- COMPARISON RESULTS --- 📊")
    print(f"PyPDF2 -> WER: {wer_pypdf2:.4f}, CER: {cer_pypdf2:.4f}, Time: {pypdf2_time:.2f}s")
    print(f"pdfplumber -> WER: {wer_pdfplumber:.4f}, CER: {cer_pdfplumber:.4f}, Time: {pdfplumber_time:.2f}s")

    # Optional: Save extracted text to files for inspection
    with open("pypdf2_output.txt", "w", encoding="utf-8") as f:
        f.write(text_pypdf2)
    with open("pdfplumber_output.txt", "w", encoding="utf-8") as f:
        f.write(text_pdfplumber)

    print("\n✅ Extraction comparison complete! Check output text files and metrics above.")

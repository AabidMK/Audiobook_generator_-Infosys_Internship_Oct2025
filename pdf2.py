import fitz  
from jiwer import wer


pdf_path = "co assignment unit-5.pdf"        
ground_truth_path = "co assignment unit-5.txt"   


with open(ground_truth_path, "r", encoding="utf-8", errors="ignore") as f:
    reference_text = f.read()


text_pymupdf = ""
with fitz.open(pdf_path) as doc:
    for page in doc:
        text_pymupdf += page.get_text("text")

error_rate = wer(reference_text, text_pymupdf)

print("Extracted Text:\n", text_pymupdf[:500], "...\n")  # show first 500 chars
print(f"Word Error Rate (WER): {error_rate:.2f}")

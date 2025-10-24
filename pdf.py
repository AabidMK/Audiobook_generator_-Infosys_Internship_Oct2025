import fitz  
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import jiwer

pdf_path = "co assignment unit-5.pdf"
ground_truth_path = "co assignment unit-5.txt"

with open(ground_truth_path, "r", encoding="utf-8") as f:
    reference_text = f.read()

text_pymupdf = ""
with fitz.open(pdf_path) as doc:
    for page in doc:
        text_pymupdf += page.get_text("text")


text_pdfplumber = ""
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text_pdfplumber += page.extract_text()


pages = convert_from_path(pdf_path)
text_tesseract = ""
for page in pages:
    text_tesseract += pytesseract.image_to_string(page)

def evaluate(name, extracted):
    wer = jiwer.wer(reference_text, extracted)
    cer = jiwer.cer(reference_text, extracted)
    print(f"{name} → WER: {wer:.3f}, CER: {cer:.3f}")

print("\n📊 PDF Extraction Benchmark Results:")
evaluate("PyMuPDF", text_pymupdf)
evaluate("PDFPlumber", text_pdfplumber)
evaluate("Tesseract (OCR)", text_tesseract)


wer_pymupdf = jiwer.wer(reference_text, text_pymupdf)
cer_pymupdf = jiwer.cer(reference_text, text_pymupdf)

wer_pdfplumber = jiwer.wer(reference_text, text_pdfplumber)
cer_pdfplumber = jiwer.cer(reference_text, text_pdfplumber)

wer_tesseract = jiwer.wer(reference_text, text_tesseract)
cer_tesseract = jiwer.cer(reference_text, text_tesseract)

print("WER/CER Comparison:")
print(f"PyMuPDF → WER: {wer_pymupdf:.3f}, CER: {cer_pymupdf:.3f}")
print(f"PDFPlumber → WER: {wer_pdfplumber:.3f}, CER: {cer_pdfplumber:.3f}")
print(f"Tesseract → WER: {wer_tesseract:.3f}, CER: {cer_tesseract:.3f}")


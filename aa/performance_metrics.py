import fitz       
import pdfplumber
from PyPDF2 import PdfReader
import jiwer         
def extract_pymupdf(pdf_path):
    text=""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text+=page.get_text("text")
    return text
def extract_pypdf2(pdf_path):
    text=""
    reader=PdfReader(pdf_path)
    for page in reader.pages:
        text+=page.extract_text() or ""
    return text
def extract_pdfplumber(pdf_path):
    text=""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
    return text
pdf_path="South of France - Cities.pdf"
gt_path="South of France - Cities.txt"
with open(gt_path, "r", encoding="utf-8") as f:
    g_t =f.read()
methods = {
    "PyMuPDF": extract_pymupdf,
    "PyPDF2": extract_pypdf2,
    "pdfplumber": extract_pdfplumber}
print("Comparing PDF extraction accuracy\n")
for name, func in methods.items():
    ex=func(pdf_path)
    wer=jiwer.wer(g_t, ex)
    cer=jiwer.cer(g_t, ex)
    print(f"{name}: WER = {wer:.3f}, CER = {cer:.3f}")

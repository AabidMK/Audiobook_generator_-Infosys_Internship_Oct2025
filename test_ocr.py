import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pdf_path = "TheRiseofPython.pdf"  # place your same PDF in same folder

images = convert_from_path(pdf_path)
print("Pages converted:", len(images))

for i, img in enumerate(images):
    text = pytesseract.image_to_string(img)
    print(f"\n--- PAGE {i+1} TEXT START ---\n")
    print(text)
    print("\n--- PAGE TEXT END ---\n")

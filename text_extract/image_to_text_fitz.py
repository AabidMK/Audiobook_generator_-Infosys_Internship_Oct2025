import fitz 
from PIL import Image
import pytesseract
import os


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_path):
    doc = fitz.open(image_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img = img.convert("L")
    text = pytesseract.image_to_string(img)

    doc.close()
    return text


def save_text_to_file(text, image_path):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_file = f"{base_name}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Extracted text saved to: {output_file}")


if __name__ == "__main__":
   
    image_path = "img.jpg"  

    print("Extracting text from image...")
    extracted_text = extract_text_from_image(image_path)

    print("\n--- Extracted Text ---\n")
    print(extracted_text)

    save_text_to_file(extracted_text, image_path)

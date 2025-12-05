import fitz  # pymupdf
import pytesseract
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import os


os.makedirs("extracted_texts", exist_ok=True)

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select PDF or Image file")


ext = os.path.splitext(file_path)[1].lower()
output_name = os.path.basename(file_path).replace(ext, ".txt")
output_path = os.path.join("extracted_texts", output_name)

if ext == ".pdf":
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()


elif ext in [".png", ".jpg", ".jpeg"]:
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)


else:
    print("Unsupported file type.")
    exit()

with open(output_path, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Text saved to {output_path}")

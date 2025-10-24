import os
import fitz  # PyMuPDF
import docx
from PIL import Image
import io

# --- PDF Extraction ---
def extract_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text

# --- DOCX Extraction ---
def extract_docx(file_path):
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n\n".join(paragraphs)

# --- TXT Extraction ---
def extract_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Image Extraction ---
def extract_images_from_pdf(file_path, output_dir="extracted_images"):
    """Extract images from PDF file"""
    image_paths = []
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # RGB
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    else:  # CMYK
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    
                    img_data = pix1.tobytes("png")
                    pix1 = None
                    pix = None
                    
                    # Save image
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    img_filename = f"{base_name}_page{page_num+1}_img{img_index+1}.png"
                    img_path = os.path.join(output_dir, img_filename)
                    
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_data)
                    
                    image_paths.append(img_path)
                    
        print(f"Extracted {len(image_paths)} images to {output_dir}")
        return image_paths
        
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")
        return []

def extract_image_text(file_path):
    """Extract text from images using OCR (basic placeholder)"""
    # Note: For actual OCR, you would need to install and use:
    # pip install pytesseract
    # And have Tesseract OCR installed on your system
    
    try:
        # This is a placeholder - implement actual OCR here
        # Example with pytesseract:
        """
        import pytesseract
        from PIL import Image
        
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
        """
        print(f"OCR extraction would be performed on: {file_path}")
        return f"[Image content from {os.path.basename(file_path)}]"
        
    except Exception as e:
        print(f"Error in OCR extraction: {e}")
        return ""

# --- Save text ---
def save_text(text, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved text to {output_path}")

# --- Main Extraction Function ---
def extract_file(file_path, output_dir="output_files", save_as_md=False, extract_images=False):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_pdf(file_path)
        if extract_images:
            extract_images_from_pdf(file_path, os.path.join(output_dir, "images"))
    elif ext == ".docx":
        text = extract_docx(file_path)
    elif ext == ".txt":
        text = extract_txt(file_path)
    elif ext.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]:
        text = extract_image_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    # Output file naming
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_ext = "md" if save_as_md else "txt"
    out_path = os.path.join(output_dir, f"{base_name}.{out_ext}")
    save_text(text, out_path)
    return out_path

# --- CLI Example ---
if __name__ == "__main__":
    file_path = input("Enter file path (PDF/DOCX/TXT/Image): ").strip()
    save_md = input("Save as markdown? (y/n): ").strip().lower()
    extract_img = input("Extract images from PDF? (y/n): ").strip().lower()
    
    extract_file(
        file_path, 
        save_as_md=(save_md == 'y'),
        extract_images=(extract_img == 'y')
    )
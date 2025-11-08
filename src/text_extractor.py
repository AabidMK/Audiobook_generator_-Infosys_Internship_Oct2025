import os
import fitz  # PyMuPDF
import docx

# --- PDF Extraction ---
def extract_pdf(file_path):
    """Extract text from PDF file"""
    print(f"📖 Extracting text from PDF: {os.path.basename(file_path)}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    text = ""
    try:
        with fitz.open(file_path) as doc:
            total_pages = len(doc)
            print(f"   Processing {total_pages} pages...")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text("text")
                text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                print(f"   ✅ Page {page_num + 1} extracted")
        
        print(f"✅ PDF extraction completed: {len(text)} characters")
        return text
        
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return ""

# --- DOCX Extraction ---
def extract_docx(file_path):
    """Extract text from DOCX file"""
    print(f"📄 Extracting text from DOCX: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        
        print(f"✅ DOCX extraction completed: {len(text)} characters")
        return text
        
    except Exception as e:
        print(f"❌ Error extracting DOCX: {e}")
        return ""

# --- TXT Extraction ---
def extract_txt(file_path):
    """Extract text from TXT file"""
    print(f"📝 Extracting text from TXT: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        print(f"✅ TXT extraction completed: {len(text)} characters")
        return text
        
    except Exception as e:
        print(f"❌ Error extracting TXT: {e}")
        return ""

# --- Image Extraction from PDF ---
def extract_images_from_pdf(file_path, output_dir="extracted_images"):
    """Extract images from PDF file"""
    print(f"🖼 Extracting images from PDF...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
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
                    print(f"   ✅ Extracted image: {img_filename}")
                    
        print(f"✅ Image extraction completed: {len(image_paths)} images")
        return image_paths
        
    except Exception as e:
        print(f"❌ Error extracting images from PDF: {e}")
        return []

def extract_image_text(file_path):
    """Working image text extraction"""
    print(f"🖼 Processing image: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Try EasyOCR first if available
        import easyocr
        reader = easyocr.Reader(['en'])
        results = reader.readtext(file_path)
        
        extracted_text = ""
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                extracted_text += text + " "
        
        if extracted_text.strip():
            print(f"✅ Image text extracted: {len(extracted_text)} characters")
            return extracted_text.strip()
        else:
            return "No text detected via EasyOCR"
            
    except ImportError:
        print("   ℹ EasyOCR not available, using manual input")
    
    # Manual description fallback
    try:
        print("   Please describe what text you see:")
        description = input("   Text in image: ")
        return f"Manual: {description}" if description.strip() else "No description"
    except:
        return f"Image: {os.path.basename(file_path)} - needs manual processing"

# --- Save text ---
def save_text(text, output_path):
    """Save extracted text to file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"💾 Saved text to {output_path}")

# --- Main Extraction Function ---
def extract_file(file_path, output_dir="output_files", save_as_md=False, extract_images=False):
    """Main function to extract text from various file formats"""
    
    print(f"\n🎯 Starting extraction process...")
    print(f"📁 Input file: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found: {file_path}")
        print("Please check:")
        print(f"1. File exists at: {os.path.abspath(file_path)}")
        print("2. Use correct path (relative or absolute)")
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    print(f"📄 File type: {ext}")

    text = ""
    
    try:
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
        
        if not text.strip():
            print("⚠ No text was extracted from the file")
            return None
        
        # Output file naming
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        out_ext = "md" if save_as_md else "txt"
        out_path = os.path.join(output_dir, f"{base_name}.{out_ext}")
        
        save_text(text, out_path)
        return out_path
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None

# --- CLI Example ---
if __name__ == "__main__":
    print("🚀 TEXT EXTRACTOR TOOL")
    print("=" * 40)
    
    # Show current directory and available files
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    print("\n📂 Files in current directory:")
    for file in os.listdir('.'):
        if os.path.isfile(file):
            print(f"   - {file}")
    
    print("\n📂 Files in input_files folder:")
    input_files_dir = "../input_files"
    if os.path.exists(input_files_dir):
        for file in os.listdir(input_files_dir):
            if os.path.isfile(os.path.join(input_files_dir, file)):
                print(f"   - {file}")
    else:
        print("   (input_files folder doesn't exist)")
    
    print("\n" + "=" * 40)
    
    # Get file path with better guidance
    file_path = input("Enter file path (PDF/DOCX/TXT/Image): ").strip()
    
    # If no path provided, suggest common locations
    if not file_path:
        print("💡 Try one of these:")
        print("   - ../input_files/sample.pdf")
        print("   - ../input_files/your_file.pdf")
        print("   - Or drag and drop your file here")
        file_path = input("Enter file path: ").strip()
    
    # Remove quotes if user drag-dropped file
    file_path = file_path.strip('"')
    
    save_md = input("Save as markdown? (y/n): ").strip().lower()
    
    # Only ask for image extraction for PDF files
    extract_img = False
    if file_path.lower().endswith('.pdf'):
        extract_img = input("Extract images from PDF? (y/n): ").strip().lower() == 'y'
    
    result = extract_file(
        file_path, 
        save_as_md=(save_md == 'y'),
        extract_images=extract_img
    )
    
    print("\n" + "=" * 40)
    if result:
        print(f"🎉 EXTRACTION COMPLETED: {result}")
    else:
        print("❌ EXTRACTION FAILED")
    print("=" * 40)
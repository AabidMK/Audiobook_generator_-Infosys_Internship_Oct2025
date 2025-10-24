import streamlit as st
import os
import tempfile
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import docx
import pdfplumber
import subprocess

# Auto-detect Tesseract installation
def find_tesseract():
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME')),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Try to find in PATH
    try:
        result = subprocess.run(["where", "tesseract"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None

# Configure Tesseract (GLOBAL VARIABLE)
tesseract_path = find_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    tesseract_available = True
else:
    tesseract_available = False

# Page configuration
st.set_page_config(
    page_title="Text Extraction Tool",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .file-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def enhance_image_for_ocr(image):
    """Enhance image using PIL only (no OpenCV required)"""
    try:
        # Convert to grayscale for better OCR
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)  # Increase sharpness
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.MedianFilter(3))
        
        return image
        
    except Exception:
        # If enhancement fails, return original image
        return image

def extract_text_from_image(file_path):
    """Extract text from images using enhanced OCR"""
    try:
        if not tesseract_available:
            return "Tesseract OCR is not installed. Please install it to extract text from images."
        
        # Open the image
        original_image = Image.open(file_path)
        
        # Get image info for quality check
        width, height = original_image.size
        
        # Show image info
        if width < 300 or height < 300:
            st.warning("⚠️ Image resolution is low. For better OCR results, use images with at least 300x300 pixels.")
        
        # Try multiple approaches
        results = []
        
        # Approach 1: Enhanced image
        enhanced_image = enhance_image_for_ocr(original_image)
        text_enhanced = pytesseract.image_to_string(enhanced_image, config='--psm 6')
        results.append(("Enhanced", text_enhanced))
        
        # Approach 2: Original image with different PSM
        text_original = pytesseract.image_to_string(original_image, config='--psm 6')
        results.append(("Original PSM6", text_original))
        
        # Approach 3: Try automatic PSM
        text_auto = pytesseract.image_to_string(original_image, config='--psm 3')
        results.append(("Auto PSM3", text_auto))
        
        # Approach 4: Try sparse text PSM
        text_sparse = pytesseract.image_to_string(original_image, config='--psm 11')
        results.append(("Sparse PSM11", text_sparse))
        
        # Find the best result
        best_text = ""
        best_length = 0
        
        for method, text in results:
            clean_text = text.strip()
            if len(clean_text) > best_length:
                best_length = len(clean_text)
                best_text = clean_text
        
        # If we found text, show which method worked best
        if best_text:
            for method, text in results:
                if text.strip() == best_text:
                    st.success(f"✓ Best OCR method: {method}")
                    break
        
        return best_text if best_text else "No text found in the image. Try a clearer image with better contrast."
        
    except Exception as e:
        return f"Error extracting from image: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from DOCX files"""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text)
        return '\n'.join(full_text) if full_text else "No text found in document."
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_pdf(file_path):
    """Extract text from PDF files"""
    try:
        full_text = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    full_text.append(f"--- Page {page_num} ---\n{text}")
        
        if full_text:
            return '\n\n'.join(full_text)
        else:
            # Try OCR if it's a scanned PDF and Tesseract is available
            if tesseract_available:
                return extract_text_from_image(file_path)
            else:
                return "No text found in PDF. This might be a scanned document. Install Tesseract OCR for scanned PDF support."
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_txt(file_path):
    """Extract text from TXT files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return text.strip() if text.strip() else "File is empty."
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.markdown('<h1 class="main-header">🚀 Advanced Text Extraction Tool</h1>', unsafe_allow_html=True)
    
    # Show Tesseract status
    if not tesseract_available:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ Tesseract OCR Not Installed</h4>
            <p>Image text extraction is not available. To enable it:</p>
            <ol>
                <li>Download Tesseract from: <a href="https://github.com/UB-Mannheim/tesseract/wiki" target="_blank">https://github.com/UB-Mannheim/tesseract/wiki</a></li>
                <li>Install it and restart this app</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Supported Formats")
        st.markdown("""
        - **Images** → JPG, PNG, BMP (OCR)
        - **PDF** → Text extraction
        - **Word** → DOCX files  
        - **Text** → TXT files
        """)
        
        st.header("⚙️ Instructions")
        st.markdown("""
        1. Upload your file
        2. Click 'Extract Text'
        3. View & download result
        """)
        
        st.markdown("---")
        st.header("📷 OCR Tips")
        st.markdown("""
        **For better image OCR:**
        - Use high-resolution images
        - Good lighting & contrast
        - Clear, standard fonts
        - Dark text on light background
        """)
        
        if tesseract_available:
            st.success(f"✅ OCR: Enabled")
        else:
            st.warning("❌ OCR: Not installed")
    
    # File upload
    st.markdown("### 📁 Upload Your Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'bmp'],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Type", uploaded_file.type)
        with col3:
            st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        # Extract button
        if st.button("🚀 Extract Text", type="primary", use_container_width=True):
            with st.spinner("Extracting text... Please wait."):
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Extract based on file type
                    file_ext = uploaded_file.name.lower().split('.')[-1]
                    
                    if file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
                        extracted_text = extract_text_from_image(tmp_path)
                    elif file_ext == 'docx':
                        extracted_text = extract_text_from_docx(tmp_path)
                    elif file_ext == 'pdf':
                        extracted_text = extract_text_from_pdf(tmp_path)
                    elif file_ext == 'txt':
                        extracted_text = extract_text_from_txt(tmp_path)
                    else:
                        st.error(f"Unsupported file type: {file_ext}")
                        return
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("### 📝 Extracted Text")
                    
                    # Statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Characters", len(extracted_text))
                    with col2:
                        st.metric("Words", len(extracted_text.split()))
                    with col3:
                        st.metric("Lines", len(extracted_text.splitlines()))
                    
                    # Text area
                    st.text_area(
                        "Extracted Content",
                        extracted_text,
                        height=400,
                        label_visibility="collapsed"
                    )
                    
                    # Download button
                    st.download_button(
                        label="📥 Download as TXT",
                        data=extracted_text,
                        file_name=f"{uploaded_file.name.split('.')[0]}_extracted.txt",
                        mime="text/plain",
                        type="primary",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Processing error: {str(e)}")
                finally:
                    # Cleanup
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    else:
        # Welcome message
        st.markdown("---")
        st.info("👆 Please upload a file to begin text extraction")

if __name__ == "__main__":
    main()
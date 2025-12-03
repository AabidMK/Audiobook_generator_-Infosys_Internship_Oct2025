import streamlit as st
import tempfile
import os
from text_extraction import extract_text_from_file, validate_extracted_text, get_file_info

st.set_page_config(
    page_title="Text Extraction Module",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .file-card {
        background: #F8FAFC;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .result-card {
        background: #F0F9FF;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #E0F2FE;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .success-box {
        background: #D1FAE5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
    }
    .error-box {
        background: #FEE2E2;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #EF4444;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📚 AI Audiobook Generator</h1>', unsafe_allow_html=True)
st.markdown('<h3 class="sub-header">Text Extraction Module - Extract text from various document formats</h3>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.info("""
    This module extracts text from:
    - 📝 TXT files
    - 📄 PDF documents  
    - 📋 DOCX files
    - 🖼️ Images (with OCR)
    """)
    
    st.markdown("### ⚙️ Settings")
    min_words = st.slider("Minimum words for validation", 1, 20, 5)
    
    st.markdown("---")
    st.markdown("### 🛠️ Dependencies")
    st.code("""
    pip install streamlit
    pip install pdfplumber
    pip install python-docx
    pip install pytesseract
    pip install Pillow
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract", "📊 File Info", "ℹ️ Documentation"])

with tab1:
    st.markdown("### 📤 Upload Your Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file to extract text from",
        type=['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'bmp'],
        help="Supported formats: Text, PDF, Word, and Images"
    )
    
    if uploaded_file:
        # File info card
        file_info = get_file_info(uploaded_file)
        
        st.markdown('<div class="file-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 File", file_info['filename'])
        with col2:
            st.metric("📊 Type", file_info['type'])
        with col3:
            st.metric("⚖️ Size", f"{file_info['size_kb']:.1f} KB")
        with col4:
            st.metric("🔤 Extension", file_info['extension'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # OCR status for images
        if file_info['extension'] in ['jpg', 'jpeg', 'png', 'bmp']:
            if file_info['ocr_available']:
                st.success("✅ OCR is available for this image")
            else:
                st.warning("⚠️ OCR not available. Install pytesseract and Tesseract OCR")
        
        # Extract button
        if st.button("🚀 Extract Text", type="primary", use_container_width=True):
            with st.spinner("🔍 Extracting text from file..."):
                # Extract text
                extracted_text = extract_text_from_file(uploaded_file)
                
                # Validate
                is_valid, message = validate_extracted_text(extracted_text, min_words=min_words)
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Extraction Results")
                
                if is_valid:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.success(f"✅ {message}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Stats
                    st.markdown("#### 📈 Text Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📝 Characters", len(extracted_text))
                    with col2:
                        st.metric("🔤 Words", len(extracted_text.split()))
                    with col3:
                        st.metric("📄 Lines", len(extracted_text.split('\n')))
                    with col4:
                        st.metric("✅ Status", "Valid")
                    
                    # Extracted text
                    st.markdown("#### 📋 Extracted Text")
                    st.text_area(
                        "Extracted Content", 
                        extracted_text, 
                        height=300,
                        label_visibility="collapsed"
                    )
                    
                    # Download button
                    st.download_button(
                        label="💾 Download Text File",
                        data=extracted_text.encode('utf-8'),
                        file_name=f"extracted_{uploaded_file.name.split('.')[0]}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                else:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"❌ {message}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.text_area(
                        "⚠️ Extraction Result", 
                        extracted_text, 
                        height=200,
                        label_visibility="collapsed"
                    )

with tab2:
    st.markdown("### 📊 File Information")
    
    if 'file_info' in locals() and uploaded_file:
        st.markdown("#### 📁 Current File Details")
        
        info_cols = st.columns(2)
        with info_cols[0]:
            st.write("**Filename:**", file_info['filename'])
            st.write("**Extension:**", file_info['extension'])
            st.write("**File Type:**", file_info['type'])
        with info_cols[1]:
            st.write("**Size:**", f"{file_info['size_kb']:.1f} KB")
            st.write("**Icon:**", file_info['icon'])
            if file_info.get('ocr_available') is not None:
                st.write("**OCR Available:**", "✅ Yes" if file_info['ocr_available'] else "❌ No")
    
    st.markdown("---")
    st.markdown("#### 📋 Supported Formats")
    
    formats_data = [
        {"Format": "📝 TXT", "Description": "Plain text files", "Library": "Built-in"},
        {"Format": "📄 PDF", "Description": "Portable Document Format", "Library": "pdfplumber"},
        {"Format": "📋 DOCX", "Description": "Microsoft Word documents", "Library": "python-docx"},
        {"Format": "🖼️ JPG/PNG", "Description": "Image files with text", "Library": "pytesseract (OCR)"},
        {"Format": "🖼️ BMP", "Description": "Bitmap image files", "Library": "pytesseract (OCR)"},
    ]
    
    for fmt in formats_data:
        with st.expander(f"{fmt['Format']} - {fmt['Description']}"):
            st.write(f"**Library:** {fmt['Library']}")
            st.write(f"**Extension:** .{fmt['Format'].split()[-1].lower()}")

with tab3:
    st.markdown("### 📚 Documentation")
    
    st.markdown("""
    #### 🎯 Module Purpose
    This Text Extraction Module is designed to extract text content from various document formats
    as part of an AI Audiobook Generator pipeline.
    
    #### 🔧 How It Works
    1. **File Upload**: User uploads a document
    2. **Format Detection**: Module identifies file type
    3. **Text Extraction**: Uses appropriate library for extraction
    4. **Validation**: Checks if extracted text is meaningful
    5. **Output**: Returns clean text for further processing
    
    #### 🏗️ Architecture
    ```
    text_extraction/
    ├── __init__.py     # Module exports
    └── extractor.py    # Core extraction logic
    ```
    
    #### 📝 API Reference
    
    **Main Functions:**
    ```python
    # Extract text from file
    text = extract_text_from_file(uploaded_file)
    
    # Validate extracted text
    is_valid, message = validate_extracted_text(text, min_words=5)
    
    # Get file information
    info = get_file_info(uploaded_file)
    ```
    
    #### 🚨 Error Handling
    - Returns informative error messages
    - Graceful degradation when libraries missing
    - Validation to filter meaningless text
    
    #### 🔄 Integration
    This module can be integrated into:
    - Streamlit apps (as shown)
    - Flask/Django web applications
    - Batch processing scripts
    - AI pipelines for text processing
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B;'>"
    "Text Extraction Module • Part of AI Audiobook Generator • Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)
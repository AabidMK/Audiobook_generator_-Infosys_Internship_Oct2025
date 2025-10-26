
import streamlit as st
import os
import tempfile
import base64
from text_extractor import EnhancedTextExtractor
from text_enhancer import TextEnhancer


def main():
    st.set_page_config(
        page_title="Convert to Audiobook ",
        page_icon="🎶",
        layout="wide"
    )

    st.title(" AudioBook Generator ")
    st.markdown("Extract text → Enhance with Google Gemini → Generate Audio")

    # Initialize components
    extractor = EnhancedTextExtractor()
    enhancer = TextEnhancer()
    

    # Sidebar: Settings
    st.sidebar.header("🔧 Enhancement Settings")
    enhancement_style = st.sidebar.selectbox(
        "Enhancement Style",
        ["engaging", "dramatic", "conversational", "professional"]
    )

    st.sidebar.markdown("---")
    st.sidebar.header("🔑 Gemini API Info")
    st.sidebar.markdown("""
    - The app automatically loads your API key from `.env`
    - Make sure `.env` file contains:  
      `GEMINI_API_KEY=your_actual_api_key_here`
    """)

    # File upload
    uploaded_file = st.file_uploader(
        "📁 Upload a file (PDF, DOCX, TXT, PNG, JPG)",
        type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg']
    )

    if uploaded_file is not None:
        # File details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**File:** {uploaded_file.name}")
        with col2:
            st.write(f"**Type:** {uploaded_file.type}")
        with col3:
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")

        # Save uploaded file to temp path
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Display image if uploaded
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext in [".png", ".jpg", ".jpeg"]:
                st.image(uploaded_file, caption="Uploaded Image")

            # Extraction options
            use_ocr = st.checkbox("Use OCR for PDFs", value=True)

            # Step 1: Extract Text
            if st.button("📖 Step 1: Extract Text", type="primary"):
                with st.spinner("Extracting text..."):
                    result = extractor.extract_text(tmp_file_path, use_ocr=use_ocr)

                if result['success']:
                    st.session_state.extraction_result = result
                    st.session_state.original_text = result['text_content']
                    st.success("✅ Text extraction completed!")

                    # Stats
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Characters", f"{result['char_count']:,}")
                    col2.metric("Words", f"{result['word_count']:,}")
                    col3.metric("Images", len(result['image_descriptions']))
                    col4.metric("Tables", len(result.get('tables', [])))

                    # Show extracted text
                    st.subheader("📄 Extracted Text")
                    st.text_area("Raw Text", result['text_content'], height=300)

                    # Download as text
                    st.download_button(
                        label="📥 Download Extracted Text",
                        data=result['text_content'],
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}.txt",
                        mime="text/plain"
                    )

                    # Image descriptions
                    if result['image_descriptions']:
                        with st.expander("🖼️ Image Descriptions"):
                            for desc in result['image_descriptions']:
                                st.write(f"• {desc}")

                else:
                    st.error(f"❌ Extraction failed: {result['error']}")

            # Step 2: Enhance Text (requires extraction)
            if 'extraction_result' in st.session_state:
                st.markdown("---")
                st.subheader("🎭 Step 2: Enhance Text with Gemini")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✨ Enhance with Gemini AI"):
                        with st.spinner("Enhancing text using Gemini..."):
                            result = enhancer.enhance_with_gemini(
                                st.session_state.original_text,
                                style=enhancement_style
                            )

                        if result['success']:
                            st.session_state.enhanced_text = result['enhanced_text']
                            st.success("✅ Text enhanced successfully!")

                            st.text_area(
                                "🎭 Enhanced Text",
                                result['enhanced_text'],
                                height=300
                            )

                            st.download_button(
                                label="📥 Download Enhanced Text",
                                data=result['enhanced_text'],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_enhanced.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error(f"❌ Enhancement failed: {result['error']}")

                with col2:
                    if st.button("🆓 Enhance with Rules (Offline Mode)"):
                        with st.spinner("Enhancing with rule-based logic..."):
                            result = enhancer.enhance_with_rules(
                                st.session_state.original_text,
                                style=enhancement_style
                            )

                        if result['success']:
                            st.session_state.enhanced_text = result['enhanced_text']
                            st.success("✅ Rule-based enhancement completed!")

                            st.text_area(
                                "🎭 Rule-Enhanced Text",
                                result['enhanced_text'],
                                height=300
                            )

                            st.download_button(
                                label="📥 Download Rule-Enhanced Text",
                                data=result['enhanced_text'],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_rule_enhanced.txt",
                                mime="text/plain"
                            )

            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    # Sidebar help
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 How to Use")
    st.sidebar.markdown("""
    1. **Upload** a file (PDF, DOCX, TXT, or Image)
    2. **Extract** text (Step 1)
    3. **Enhance** text using Gemini AI (Step 2)
    4. **Generate** audiobook (Step 3)
    """)


if __name__ == "__main__":
    main()

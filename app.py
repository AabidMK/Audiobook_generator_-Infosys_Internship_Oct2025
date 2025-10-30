import streamlit as st
import google.generativeai as genai
import pdfplumber
import pytesseract
from PIL import Image
import os

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyB6Ev_MuYb1cyovoYjEyb1DOrOlTWWbmFI")

# File upload UI
st.title("📘 AI Audiobook Generator")
uploaded_file = st.file_uploader("Upload your PDF or image file", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    filename = uploaded_file.name
    with open(filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Uploaded: {filename}")

    extracted_text = ""
    # Extract text
    if filename.endswith(".pdf"):
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""
    else:
        image = Image.open(filename)
        extracted_text = pytesseract.image_to_string(image)

    st.subheader("📄 Extracted Text")
    st.text_area("Text", extracted_text, height=200)

    if st.button("✨ Enrich Text with Gemini AI"):
        system_prompt = (
            "You are a helpful AI that rewrites text to make it clearer, more professional, "
            "and human-like without losing meaning. Keep formatting natural."
        )

        model = genai.GenerativeModel("models/gemini-2.5-pro")
        response = model.generate_content(system_prompt + "\n\n" + extracted_text)
        enriched_text = response.text.strip()

        st.subheader("💡 Enriched Text")
        st.text_area("Enhanced Output", enriched_text, height=250)

        # Save output
        output_path = "enriched_text.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(enriched_text)
        st.success(f"✅ Enriched text saved to {output_path}")


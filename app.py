import streamlit as st
import google.generativeai as genai
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
import os

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyB6Ev_MuYb1cyovoYjEyb1DOrOlTWWbmFI")

# Streamlit App UI
st.title("📘 AI Audiobook Generator - Text Extraction & Enrichment")

uploaded_file = st.file_uploader(
    "Upload your PDF, Image, Word, or Text file",
    type=["pdf", "png", "jpg", "jpeg", "docx", "txt"]
)

if uploaded_file:
    filename = uploaded_file.name
    with open(filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Uploaded: {filename}")

    extracted_text = ""

    # ---------- TEXT EXTRACTION ----------
    if filename.endswith(".pdf"):
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

    elif filename.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(filename)
        extracted_text = pytesseract.image_to_string(image)

    elif filename.endswith(".docx"):
        doc = Document(filename)
        for para in doc.paragraphs:
            extracted_text += para.text + "\n"

    elif filename.endswith(".txt"):
        with open(filename, "r", encoding="utf-8") as f:
            extracted_text = f.read()

    else:
        st.error("Unsupported file format.")
        st.stop()

    # ---------- DISPLAY EXTRACTED TEXT ----------
    st.subheader("📄 Extracted Text")
    st.text_area("Extracted Text", extracted_text, height=200)

    # ---------- TEXT ENRICHMENT ----------
    if st.button("✨ Enrich Text with Gemini AI"):
        system_prompt = (
            "Rewrite the following text clearly and professionally.\n"
            "Do not include options or explanations — return only one improved version.\n"
            "Keep the tone natural and fluent."
        )

        model = genai.GenerativeModel("models/gemini-2.5-pro")
        response = model.generate_content(system_prompt + "\n\n" + extracted_text)
        enriched_text = response.text.strip()

        # ---------- DISPLAY & SAVE ENRICHED TEXT ----------
        st.subheader("💡 Enriched Text")
        st.text_area("Enhanced Output", enriched_text, height=250)

        output_path = "enriched_text.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(enriched_text)
        st.success(f"✅ Enriched text saved to {output_path}")



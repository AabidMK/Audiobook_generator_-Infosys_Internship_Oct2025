from text_extractor import extract_text  # same folder import

def run_pipeline(file_path, output_path=None):
    """
    Extract text from PDF/DOCX/TXT file.
    Optionally save extracted text to a file.
    """
    text = extract_text(file_path)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

    return text

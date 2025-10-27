from docx import Document

def extract_text_from_word(file_path):
    """
    Extract text directly from a .docx Word file.
    """
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


# Example usage
if __name__ == "__main__":
    word_file = "maulik.docx"
    text_content = extract_text_from_word(word_file)
    print("\nExtracted Text:\n")
    print(text_content)


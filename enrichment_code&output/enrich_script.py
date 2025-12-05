import os
import tkinter as tk
from tkinter import filedialog
from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """
You are an expert content editor and professional narrator for audiobooks, specialized in informational and technical subjects. 
Your task is to rewrite the provided raw, extracted text into a clear, engaging, and polished script optimized for a smooth AI reading.

Your output must strictly adhere to the following rules:

1.  Conversational Flow: Rewrite long or complex sentences into shorter, clearer, and more conversational prose.
2.  Audience Tone: Maintain a friendly, professional, and slightly energetic tone suitable for a learning-focused audience.
3.  Artifact Removal: **CRITICAL:** Completely remove any PDF-extraction junk like page numbers, inconsistent line breaks, hyphens splitting words (e.g., 're-write'), headers, or footnotes.
4.  Structural Clarity: Group related sentences into logical paragraphs. Use an extra blank line between paragraphs to create natural breaks for the narrator. Do NOT use markdown headings (##) or bullet points (*) in the final output, as the Text-to-Speech engine needs clean, flowing text.
5.  Enhancement: Add brief, simple analogies or introductory phrases (e.g., "Let's explore...") to ease the listener into complex topics.
"""

def enrich_text_for_audiobook():
    """Reads a file, calls the Gemini API for enrichment, and saves the result."""
   
    try:
        client = genai.Client()
    except Exception as e:
        print("ERROR: Failed to initialize Gemini Client.")
        print("Please ensure your GEMINI_API_KEY environment variable is set correctly.")
        print(f"Details: {e}")
        return

    print("A file selection window will now pop up. Please select your raw .txt file.")
    
    root = tk.Tk()
    root.withdraw() 
    
    input_file_path = filedialog.askopenfilename(
        title="Select the Raw Extracted .txt File (Module 1 Output)",
        filetypes=[("Text files", "*.txt")]
    )

    if not input_file_path:
        print("No file selected. Exiting script.")
        return

    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        print(f"Reading input file: {input_file_path}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    if not raw_text.strip():
        print("The selected file is empty. Exiting.")
        return

    print("--- Calling Gemini API for Enrichment (This may take a moment) ---")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Fast, cost-effective, and powerful enough for this task
            contents=[raw_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        enriched_text = response.text
        
        base_name = os.path.basename(input_file_path).replace('.txt', '')
        output_file_name = f"{base_name}_enriched_script.txt"
        
        output_dir = os.path.dirname(input_file_path)
        output_file_path = os.path.join(output_dir, output_file_name)
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(enriched_text)

        print("\n✅ Enrichment Complete!")
        print(f"Output saved to: {output_file_path}")
        print("\nReady for Module 3: Text-to-Speech (TTS) Conversion.")

    except Exception as e:
        print(f"\nAPI Error: An error occurred during the call to the Gemini API. {e}")
        print("Check your internet connection, API key validity, and usage limits.")

if __name__ == "__main__":
    enrich_text_for_audiobook()
# main.py

import os
import sys
from text_extraction import extract_and_save  # Step 1
from text_enrichment import enrich_text       # Step 2

# === NEW IMPORT ===
# Import the new function from your piper_tts.py file
from piper_tts import generate_and_save_audio # Step 3
# ==================

def read_text_file(file_path):
    """Simple helper to read text content from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

# ========================================
# Command-line Entry
# ========================================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <input_file>")
        print("Supported types: .pdf, .docx, .png, .jpg, etc.")
        sys.exit(1)

    input_file = sys.argv[1]
    base_name = os.path.splitext(input_file)[0]

    # ------------------------------------
    # Step 1: Extract text from source file
    # ------------------------------------
    print("🔹 Step 1: Extracting text from file...")
    extracted_txt_file = extract_and_save(input_file)

    if not extracted_txt_file:
        print("⚠️ Extraction failed. No text to enrich.")
        sys.exit(1)

    # ------------------------------------
    # Step 2: Enrich extracted text for narration
    # ------------------------------------
    print("🔹 Step 2: Enriching extracted text...")
    enriched_file = enrich_text(extracted_txt_file)

    if not enriched_file:
        print("⚠️ Enrichment failed. No audio to generate.")
        sys.exit(1)

    # ------------------------------------
    # Step 3: Generate audio from enriched text (Simplified)
    # ------------------------------------
    print("🔹 Step 3: Generating audio from enriched text...")
    
    # Read the final, enriched text
    text_to_speak = read_text_file(enriched_file)
    
    if text_to_speak:
        # Define the final audio filename
        final_audio_file = f"{base_name}_final_audio.wav"
        
        # Call the new function to generate and save the file directly
        success = generate_and_save_audio(text_to_speak, final_audio_file)
        
        if success:
            print(f"\n🎉 All done! Final audio saved to '{final_audio_file}'")
        else:
            print("⚠️ TTS generation failed.")
    else:
        print(f"⚠️ Could not read text from '{enriched_file}'.")

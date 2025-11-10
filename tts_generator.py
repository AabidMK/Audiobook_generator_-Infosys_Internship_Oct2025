import os
import glob
import edge_tts
import asyncio

# --- Configuration ---
TXT_FOLDER = "output_text_enrichment"
COMBINED_TEXT_FILE = "enriched_text_for_tts.txt"
AUDIO_OUTPUT_FILE = "audiobook.mp3"

def combine_txt_files():
    """Combine all TXT files in the folder into one text file."""
    if not os.path.exists(TXT_FOLDER):
        raise FileNotFoundError(f"Folder '{TXT_FOLDER}' not found.")
    
    txt_files = glob.glob(os.path.join(TXT_FOLDER, "*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No TXT files found in '{TXT_FOLDER}'.")

    print(f"🔎 Found {len(txt_files)} TXT file(s). Combining text...")
    all_text = []

    for file_path in txt_files:
        print(f"Processing: {os.path.basename(file_path)}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            all_text.append(text)
            all_text.append("\n\n--- FILE BREAK ---\n\n")

    final_text = "".join(all_text).strip()
    with open(COMBINED_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)
    
    print(f"✅ Combined text saved to '{COMBINED_TEXT_FILE}'")
    return final_text

async def convert_text_to_speech(text):
    """Convert text to speech using Microsoft Edge TTS."""
    print("🎧 Generating speech... please wait...")
    tts = edge_tts.Communicate(text, "en-US-AriaNeural")
    await tts.save(AUDIO_OUTPUT_FILE)
    print(f"✅ Audio saved as '{AUDIO_OUTPUT_FILE}'")

if __name__ == "__main__":
    try:
        text = combine_txt_files()
        asyncio.run(convert_text_to_speech(text))
    except Exception as e:
        print(f"⚠️ Error: {e}")

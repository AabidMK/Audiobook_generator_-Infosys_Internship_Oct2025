import os
from extractor import extract_text_from_file
from llm_enrich import TextEnricher
from tts import generate_audiobook_from_text

# === Pipeline Config ===
UPLOAD_DIR = "uploads"
TEXT_OUTPUT_DIR = "output_text"
AUDIO_OUTPUT_DIR = "output_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEXT_OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

def run_pipeline(file_path: str):
    print("📌 Starting audiobook generation pipeline...")

    # Step 1️⃣ Extract text
    print("\n📙 Step 1: Extracting text...")
    extracted_text = extract_text_from_file(file_path)

    extracted_path = os.path.join(
        TEXT_OUTPUT_DIR,
        os.path.splitext(os.path.basename(file_path))[0] + "_extracted.txt"
    )
    with open(extracted_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    print(f"✔ Text extracted: {extracted_path}")

    # Step 2️⃣ Enrich text for high quality TTS
    print("\n📝 Step 2: Enriching text...")
    enricher = TextEnricher()
    enriched_text = enricher.enrich_text(extracted_text)

    enriched_path = os.path.join(
        TEXT_OUTPUT_DIR,
        os.path.splitext(os.path.basename(file_path))[0] + "_enriched.txt"
    )
    with open(enriched_path, "w", encoding="utf-8") as f:
        f.write(enriched_text)
    print(f"✔ Text enriched: {enriched_path}")

    # Step 3️⃣ Convert enriched text → Audio
    print("\n🎧 Step 3: Converting to audiobook...")
    audio_output_path = generate_audiobook_from_text(enriched_text, AUDIO_OUTPUT_DIR)

    print("\n🎉 Pipeline Complete!")
    print(f"📢 Audiobook saved at: {audio_output_path}")

    return enriched_path, audio_output_path





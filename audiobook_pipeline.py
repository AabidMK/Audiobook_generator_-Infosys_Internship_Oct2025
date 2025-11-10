
import os
import asyncio
from extractor_module import TextExtractor
from text_enrichment import TextEnricher
from tts_generator import convert_text_to_speech

EXTRACT_FORMAT = 'txt'
ENRICHMENT_STYLE = "professional, engaging, and suitable for audiobook narration"
AUDIO_OUTPUT_FILE = "audiobook.mp3"


async def main():
    print("\n============================")
    print(" UNIVERSAL AUDIOBOOK MAKER")
    print("============================\n")

   
    input_path = input(" Enter the file path (PDF, DOCX, TXT, PNG, JPG): ").strip()

    if not os.path.exists(input_path):
        print(f" File not found: {input_path}")
        return

    base_name = os.path.splitext(os.path.basename(input_path))[0]


    print("\n Step 1: Extracting text...")
    extractor = TextExtractor()
    extracted_text = extractor.extract_text(input_path)

    if extracted_text.startswith("Error") or not extracted_text.strip():
        print(f"Extraction failed: {extracted_text}")
        return

    extracted_file = f"{base_name}_extracted_text.{EXTRACT_FORMAT}"
    with open(extracted_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    print(f" Extracted text saved to: {extracted_file}")

    print("\n Step 2: Enriching text...")
    enricher = TextEnricher()
    system_prompt = enricher.generate_system_prompt(target_style=ENRICHMENT_STYLE)
    enriched_text = enricher.rewrite_text(extracted_text, system_prompt)

    if enriched_text.startswith("Error") or not enriched_text.strip():
        print(f" Enrichment failed: {enriched_text}")
        return

    enriched_file = f"{base_name}_enriched.txt"
    with open(enriched_file, "w", encoding="utf-8") as f:
        f.write(enriched_text)
    print(f" Enriched text saved to: {enriched_file}")

    print("\n Step 3: Generating audiobook...")
    await convert_text_to_speech(enriched_text)
    print(f" Audiobook saved as: {AUDIO_OUTPUT_FILE}")

    print("\n PROCESS COMPLETE!")
    print(f"Files generated:\n - {extracted_file}\n - {enriched_file}\n - {AUDIO_OUTPUT_FILE}")



if __name__ == "__main__":
    asyncio.run(main())

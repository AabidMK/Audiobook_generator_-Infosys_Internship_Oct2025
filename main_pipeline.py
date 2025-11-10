
import os
import asyncio
from extractor_module import TextExtractor
from text_enrichment import TextEnricher
from tts_generator import convert_text_to_speech


FILES_TO_PROCESS = [
    "Sample 1.docx",
    "Sample 2.pdf",
    "sample 3.txt",
    "sample 4.jpg"
]
EXTRACT_FORMAT = 'txt'
ENRICHMENT_STYLE = "professional, engaging, and suitable for audiobook narration"
AUDIO_OUTPUT_FILE = "audiobook.mp3"


async def main():
    print("\n==========================")
    print("TEXT-TO-AUDIOBOOK PIPELINE")
    print("==========================\n")


    print(" Step 1: Extracting text...")
    extractor = TextExtractor()
    extracted_files = []

    for file_path in FILES_TO_PROCESS:
        text = extractor.extract_text(file_path)
        if text and not text.startswith("Error"):
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}_extracted_text.{EXTRACT_FORMAT}"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            extracted_files.append(output_path)
            print(f" Extracted: {output_path}")
        else:
            print(f"Skipped {file_path}: {text}")

    if not extracted_files:
        print(" No files were successfully extracted. Exiting.")
        return

   
    print("\n Step 2: Enriching text...")
    enricher = TextEnricher()
    enriched_files = []

    for extracted_file in extracted_files:
        print(f"→ Enriching {extracted_file}")
        base_name = os.path.splitext(extracted_file)[0].replace("_extracted_text", "")
        enriched_file = f"{base_name}_enriched.txt"

        with open(extracted_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        prompt = enricher.generate_system_prompt(target_style=ENRICHMENT_STYLE)
        enriched_text = enricher.rewrite_text(raw_text, prompt)

        with open(enriched_file, "w", encoding="utf-8") as f:
            f.write(enriched_text)
        enriched_files.append(enriched_file)
        print(f" Enriched text saved to: {enriched_file}")

    if not enriched_files:
        print(" No enriched files generated. Exiting.")
        return

    print("\n Step 3: Generating audiobook...")
    combined_text = ""
    for file_path in enriched_files:
        with open(file_path, "r", encoding="utf-8") as f:
            combined_text += f.read() + "\n\n"

    await convert_text_to_speech(combined_text)
    print(f" Audiobook ready: {AUDIO_OUTPUT_FILE}")

    print("\n PIPELINE COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
from text_extraction import extract_and_save  # make sure text_extraction.py is in same folder
from text_enrichment import enrich_text       # make sure text_enrichment.py is in same folder

# ========================================
# Command-line Entry
# ========================================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_and_enrich.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Step 1: Extract text
    print("🔹 Step 1: Extracting text from file...")
    extracted_txt_file = extract_and_save(input_file)

    if extracted_txt_file:
        # Step 2: Enrich text
        print("🔹 Step 2: Enriching extracted text...")
        enriched_file = enrich_text(extracted_txt_file)

        if enriched_file:
            print(f"🎉 All done! Enriched text saved to '{enriched_file}'")
        else:
            print("⚠️ Enrichment failed.")
    else:
        print("⚠️ Extraction failed. No text to enrich.")

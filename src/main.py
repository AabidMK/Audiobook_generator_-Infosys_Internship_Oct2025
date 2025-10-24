import os
import sys
from text_extractor import extract_file
from text_enrichment import process_text_enrichment

def create_audiobook_pipeline(input_file, output_base="output_files", 
                            use_gemini=True, api_key=None):
    """
    Complete audiobook generation pipeline:
    1. Text Extraction → 2. Text Enrichment
    """
    print("=" * 60)
    print("🎧 AUDIOBOOK GENERATOR PIPELINE")
    print("=" * 60)
    
    # Step 1: Text Extraction
    print("\n📖 STEP 1: TEXT EXTRACTION")
    print("-" * 30)
    
    extracted_path = extract_file(
        file_path=input_file,
        output_dir=os.path.join(output_base, "extracted"),
        save_as_md=False,
        extract_images=False
    )
    
    if not extracted_path or not os.path.exists(extracted_path):
        print("❌ Text extraction failed!")
        return None
    
    print(f"✅ Extraction successful: {extracted_path}")
    
    # Step 2: Text Enrichment
    print("\n🔮 STEP 2: TEXT ENRICHMENT")
    print("-" * 30)
    
    model_type = "gemini" if use_gemini else "local"
    enriched_path = process_text_enrichment(
        input_file=extracted_path,
        output_dir=os.path.join(output_base, "enriched"),
        api_key=api_key,
        model_type=model_type
    )
    
    if not enriched_path or not os.path.exists(enriched_path):
        print("❌ Text enrichment failed!")
        return None
    
    print(f"✅ Enrichment successful: {enriched_path}")
    
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    return {
        'extracted': extracted_path,
        'enriched': enriched_path
    }

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file> [output_directory]")
        print("Example: python main.py input_files/sample.pdf output_files")
        return
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_files"
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found!")
        return
    
    # Get API key from environment or user
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠  GEMINI_API_KEY not found in environment.")
        use_gemini = input("Use Gemini API? (y/n): ").lower().strip() == 'y'
        if use_gemini:
            api_key = input("Enter your Gemini API key: ").strip()
    else:
        use_gemini = True
    
    # Run the pipeline
    results = create_audiobook_pipeline(
        input_file=input_file,
        output_base=output_dir,
        use_gemini=use_gemini,
        api_key=api_key
    )
    
    if results:
        print("\n📊 RESULTS SUMMARY:")
        print(f"📄 Extracted text: {results['extracted']}")
        print(f"🔮 Enriched text: {results['enriched']}")
    else:
        print("\n💥 Pipeline failed!")

if __name__ == "__main__":
    main()
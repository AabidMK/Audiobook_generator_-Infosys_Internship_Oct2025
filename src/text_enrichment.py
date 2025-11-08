import os
import shutil

def process_text_enrichment(input_file, output_dir="enriched_output", **kwargs):
    """
    Simple text enrichment that just copies the file for now
    """
    print(f"🎯 Starting Text Enrichment Process...")
    print(f"📁 Input file: {input_file}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy the file to enriched location
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_enriched.txt")
    
    shutil.copy2(input_file, output_file)
    
    print(f"✅ Enriched text saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    # Test function
    result = process_text_enrichment("sample.txt")
    print(f"Result: {result}")
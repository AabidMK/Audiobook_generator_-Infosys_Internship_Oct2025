import os
import fitz
from audiobook_generator import AudiobookGenerator
import re

print("🎧 SIMPLE LONG AUDIOBOOK GENERATOR")
print("=" * 50)

def split_text_into_chunks(text, max_chars=4000):
    """Split text into chunks that Google TTS can handle"""
    print(f"📖 Splitting {len(text)} characters into chunks...")
    
    # Split by sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    print(f"✓ Split into {len(chunks)} chunks")
    return chunks

def main():
    # Find PDF files
    pdf_files = []
    for folder in ["../input_files", "../enriched_output"]:
        if os.path.exists(folder):
            print(f"📁 Scanning: {folder}")
            for file in os.listdir(folder):
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(folder, file)
                    pdf_files.append(pdf_path)
                    print(f"  ✓ Found: {file}")
    
    if not pdf_files:
        print("❌ No PDF files found!")
        input("Press Enter to exit...")
        return
    
    print(f"\n📋 Found {len(pdf_files)} PDF files:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {os.path.basename(pdf_file)}")
    
    try:
        choice = int(input(f"\nSelect PDF to convert (1-{len(pdf_files)}): "))
        selected_pdf = pdf_files[choice-1]
        
        print(f"\n🔄 Processing: {os.path.basename(selected_pdf)}")
        
        # Extract text from PDF
        doc = fitz.open(selected_pdf)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        
        print(f"✓ Extracted {len(text)} characters")
        
        # Show text preview
        if len(text) > 200:
            print(f"📄 Preview: {text[:200]}...")
        
        # Check if text is too long
        if len(text) > 5000:
            print("📚 Long text detected - splitting into chunks...")
            
            # Split text into chunks
            chunks = split_text_into_chunks(text)
            
            # Generate audio for each chunk
            generator = AudiobookGenerator()
            output_files = []
            
            for i, chunk in enumerate(chunks, 1):
                print(f"\n🎧 Generating chunk {i}/{len(chunks)}...")
                chunk_file = f"../output_files/chunk_{i}.mp3"
                
                # Generate this chunk (limit to 4000 chars to be safe)
                chunk_text = chunk[:4000] if len(chunk) > 4000 else chunk
                result = generator.generate_online(chunk_text, chunk_file)
                
                if result:
                    output_files.append(chunk_file)
                    print(f"✓ Saved: {chunk_file}")
                else:
                    print(f"❌ Failed to generate chunk {i}")
            
            print(f"\n✅ Generated {len(output_files)} audio chunks!")
            print("📁 Files saved in output_files folder:")
            for file in output_files:
                print(f"  - {os.path.basename(file)}")
                
            # Create a combined version info
            base_name = os.path.splitext(os.path.basename(selected_pdf))[0]
            combined_info = f"../output_files/{base_name}_COMBINE_THESE_FILES.txt"
            
            with open(combined_info, 'w') as f:
                f.write("Combine these files in order:\n")
                for file in output_files:
                    f.write(f"{os.path.basename(file)}\n")
            
            print(f"📋 Combination guide: {os.path.basename(combined_info)}")
            
        else:
            # Short text - normal processing
            base_name = os.path.splitext(os.path.basename(selected_pdf))[0]
            output_file = f"../output_files/{base_name}_audiobook.mp3"
            os.makedirs("../output_files", exist_ok=True)
            
            generator = AudiobookGenerator()
            result = generator.generate_online(text, output_file)
            
            if result:
                print(f"\n✅ Audiobook generated!")
                print(f"📁 File saved: {output_file}")
                
                play = input("\n🎵 Play the audiobook? (y/n): ").lower()
                if play == 'y':
                    generator.play_audio(output_file)
            else:
                print("❌ Failed to generate audiobook")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Program finished!")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
import os
import fitz
from audiobook_generator import AudiobookGenerator

print("🎧 SIMPLE PDF TO AUDIOBOOK CONVERTER")
print("=" * 50)

def main():
    pdf_path = "../input_files/book.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ book.pdf not found!")
        print("Please make sure book.pdf is in the input_files folder")
        input("Press Enter to exit...")
        return
    
    print("📄 Found: book.pdf")
    
    # Extract text from PDF
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        # Get text from first 3 pages for testing
        for i in range(min(3, len(doc))):
            page = doc.load_page(i)
            page_text = page.get_text().strip()
            if page_text:
                text += page_text + "\n"
                print(f"✓ Page {i+1}: {len(page_text)} characters")
        
        doc.close()
        
        if not text.strip():
            print("❌ No text found in PDF")
            return
        
        print(f"📊 Total extracted: {len(text)} characters")
        
        # Generate audio
        output_file = "book_audiobook.mp3"  # Save in current directory
        
        generator = AudiobookGenerator()
        print("🔄 Generating audiobook...")
        result = generator.generate_online(text, output_file)
        
        if result:
            print(f"✅ SUCCESS! Audiobook saved: {output_file}")
            
            # Show final file info
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / 1024  # KB
                print(f"📊 Final file size: {file_size:.1f} KB")
            
            play = input("\n🎵 Play audiobook? (y/n): ").lower()
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
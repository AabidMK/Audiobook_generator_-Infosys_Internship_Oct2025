import os
import fitz
from edge_tts_simple import EdgeTTSSimple

print("🎧 SIMPLE PDF TO AUDIOBOOK WITH EDGE TTS")
print("=" * 50)

def main():
    pdf_path = "../input_files/audiobook.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ audiobook.pdf not found!")
        input("Press Enter to exit...")
        return
    
    print("📄 Found: audiobook.pdf")
    
    # Available voices
    voices = [
        "en-US-AriaNeural",    # Most popular female voice
        "en-US-JennyNeural",   # Friendly female voice
        "en-US-GuyNeural",     # Male voice
    ]
    
    print("\n🎙  Available voices:")
    for i, voice in enumerate(voices, 1):
        print(f"  {i}. {voice}")
    
    try:
        voice_choice = int(input(f"\nSelect voice (1-{len(voices)}): "))
        selected_voice = voices[voice_choice-1]
        
        # Extract text from PDF
        doc = fitz.open(pdf_path)
        text = ""
        
        print(f"\n📖 Extracting text...")
        for i in range(len(doc)):  # All pages
            page = doc.load_page(i)
            page_text = page.get_text().strip()
            if page_text:
                text += page_text + "\n"
                if (i + 1) % 5 == 0:  # Show progress every 5 pages
                    print(f"  ✓ Processed {i+1} pages...")
        
        doc.close()
        
        if not text.strip():
            print("❌ No text found in PDF!")
            return
        
        print(f"📊 Total text extracted: {len(text)} characters")
        
        # Show text preview
        if len(text) > 200:
            print(f"📄 Preview: {text[:200]}...")
        
        # Generate audiobook
        generator = EdgeTTSSimple(voice=selected_voice)
        output_file = f"audiobook_edge_tts.mp3"
        
        print(f"\n🎧 Generating audiobook with {selected_voice}...")
        print("This may take a moment for long texts...")
        
        result = generator.generate_audio(text, output_file)
        
        if result:
            print(f"✅ SUCCESS! Audiobook saved: {output_file}")
            
            # Show file info
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                print(f"📊 File size: {file_size:.2f} MB")
            
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
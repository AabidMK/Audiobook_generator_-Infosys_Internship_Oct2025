import os
from universal_text_extractor import UniversalTextExtractor, scan_input_folders
from audiobook_generator import AudiobookGenerator

def main():
    print("🎧 UNIVERSAL FILE TO AUDIOBOOK CONVERTER")
    print("=" * 60)
    
    # Initialize components
    extractor = UniversalTextExtractor()
    audio_generator = AudiobookGenerator()
    
    # Scan for files in all input folders
    print("\n🔍 Scanning for files in input folders...")
    all_files = scan_input_folders()
    
    if not all_files:
        print("❌ No supported files found in input folders!")
        print("Supported formats: PDF, DOCX, TXT, JPG, PNG, BMP")
        return
    
    # Display found files
    print(f"\n📋 Found {len(all_files)} supported files:")
    for i, file_path in enumerate(all_files, 1):
        folder_name = os.path.basename(os.path.dirname(file_path))
        print(f"  {i}. [{folder_name}] {os.path.basename(file_path)}")
    
    # Let user choose file
    try:
        choice = int(input(f"\nSelect file to convert (1-{len(all_files)}): "))
        selected_file = all_files[choice-1]
        
        print(f"\n🔄 Processing: {os.path.basename(selected_file)}")
        
        # Extract text from file
        text = extractor.extract_text(selected_file)
        
        if not text:
            print("❌ Could not extract text from file")
            return
        
        print(f"📝 Extracted text length: {len(text)} characters")
        
        # Show first 200 characters of extracted text
        if len(text) > 200:
            print(f"📄 Text preview: {text[:200]}...")
        else:
            print(f"📄 Text: {text}")
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(selected_file))[0]
        output_file = f"../output_files/{base_name}_audiobook.mp3"
        
        # Ensure output directory exists
        os.makedirs("../output_files", exist_ok=True)
        
        print(f"\n🎧 Generating audiobook...")
        print(f"📁 Output file: {output_file}")
        
        # Generate audiobook
        result = audio_generator.generate_online(text, output_file)
        
        if result:
            print(f"\n✅ Audiobook generation complete!")
            print(f"📁 File saved: {output_file}")
            
            # Ask to play
            play = input("\n🎵 Play the audiobook? (y/n): ").lower()
            if play == 'y':
                audio_generator.play_audio(output_file)
        else:
            print("❌ Audiobook generation failed!")
            
    except (ValueError, IndexError):
        print("❌ Invalid choice")
    except Exception as e:
        print(f"❌ Error: {e}")

def batch_convert():
    """Convert all files in a folder to audiobooks"""
    print("\n🔄 BATCH CONVERSION MODE")
    print("=" * 40)
    
    extractor = UniversalTextExtractor()
    audio_generator = AudiobookGenerator()
    
    folder = input("Enter folder path (or press Enter for '../input_files'): ").strip()
    if not folder:
        folder = "../input_files"
    
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return
    
    print(f"\n📁 Scanning: {folder}")
    files = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file.lower())[1]
            if ext in ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.bmp']:
                files.append(file_path)
    
    if not files:
        print("❌ No supported files found!")
        return
    
    print(f"Found {len(files)} files to convert:")
    for file in files:
        print(f"  - {os.path.basename(file)}")
    
    confirm = input(f"\nConvert all {len(files)} files? (y/n): ").lower()
    if confirm != 'y':
        return
    
    success_count = 0
    for file_path in files:
        try:
            print(f"\n🔄 Processing: {os.path.basename(file_path)}")
            
            text = extractor.extract_text(file_path)
            if text:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_file = f"../output_files/{base_name}_audiobook.mp3"
                
                audio_generator.generate_online(text, output_file)
                success_count += 1
                print(f"✅ Converted: {os.path.basename(file_path)}")
            else:
                print(f"❌ Failed to extract text: {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"❌ Error converting {os.path.basename(file_path)}: {e}")
    
    print(f"\n🎉 Batch conversion complete!")
    print(f"✅ Successfully converted: {success_count}/{len(files)} files")

if __name__ == "__main__":
    print("UNIVERSAL FILE TO AUDIOBOOK CONVERTER")
    print("1. Convert single file")
    print("2. Batch convert all files in folder")
    
    try:
        choice = input("Choose option (1 or 2): ").strip()
        
        if choice == "2":
            batch_convert()
        else:
            main()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
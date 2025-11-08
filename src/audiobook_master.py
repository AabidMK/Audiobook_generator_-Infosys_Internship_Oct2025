import fitz  # PyMuPDF
import asyncio
import edge_tts
import os
import re
from datetime import datetime

print("🎯 AUDIOBOOK MASTER - EXTRACTED + ENRICHED + AUDIO")
print("=" * 60)

class AudiobookMaster:
    def __init__(self, voice="en-US-AriaNeural", rate="+0%"):
        self.voice = voice
        self.rate = rate
        self.output_dir = "output_files"
        self.setup_directories()
    
    def setup_directories(self):
        """Create all necessary directories"""
        print("📁 CREATING OUTPUT DIRECTORIES...")
        
        directories = [
            self.output_dir,
            os.path.join(self.output_dir, "extracted"),
            os.path.join(self.output_dir, "enriched"), 
            os.path.join(self.output_dir, "audio"),
            os.path.join(self.output_dir, "reports")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ {directory}")
        
        print("✅ All directories ready!")
    
    def extract_and_save_text(self, pdf_path):
        """Extract text from PDF and save to file"""
        print(f"\n📖 EXTRACTING TEXT FROM: {os.path.basename(pdf_path)}")
        
        try:
            if not os.path.exists(pdf_path):
                print(f"❌ PDF not found: {pdf_path}")
                return None
            
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += f"--- PAGE {page_num + 1} ---\n{text}\n\n"
                print(f"   ✅ Page {page_num + 1} extracted")
            
            doc.close()
            
            # Save extracted text
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            extracted_file = os.path.join(self.output_dir, "extracted", f"{base_name}_EXTRACTED.txt")
            
            with open(extracted_file, 'w', encoding='utf-8') as f:
                f.write("EXTRACTED TEXT DOCUMENT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Source: {pdf_path}\n")
                f.write(f"Extracted: {datetime.now()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(full_text)
            
            print(f"✅ EXTRACTED TEXT SAVED: {extracted_file}")
            print(f"📊 Characters extracted: {len(full_text)}")
            
            return full_text, base_name
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return None, None
    
    def enrich_and_save_text(self, text, base_name):
        """Enrich text and save to file"""
        print(f"\n🔧 ENRICHING TEXT...")
        
        if not text:
            return None
        
        # Simple text enrichment
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\s.,!?]', '', text)
        
        # Basic sentence capitalization
        sentences = text.split('. ')
        enriched_sentences = []
        for sentence in sentences:
            if sentence and sentence[0].isalpha():
                sentence = sentence[0].upper() + sentence[1:]
            enriched_sentences.append(sentence)
        text = '. '.join(enriched_sentences)
        
        # Save enriched text
        enriched_file = os.path.join(self.output_dir, "enriched", f"{base_name}_ENRICHED.txt")
        
        with open(enriched_file, 'w', encoding='utf-8') as f:
            f.write("ENRICHED TEXT DOCUMENT\n")
            f.write("=" * 50 + "\n")
            f.write("Processing applied:\n")
            f.write("• Whitespace cleaning\n• Special character removal\n")
            f.write("• Sentence capitalization\n")
            f.write("=" * 50 + "\n\n")
            f.write(text)
        
        print(f"✅ ENRICHED TEXT SAVED: {enriched_file}")
        print(f"📊 Characters after enrichment: {len(text)}")
        
        return text
    
    async def create_audio(self, text, base_name):
        """Create audio from text"""
        print(f"\n🎵 CREATING AUDIOBOOK...")
        
        try:
            audio_file = os.path.join(self.output_dir, "audio", f"{base_name}_AUDIOBOOK.mp3")
            
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate
            )
            
            print("⏳ Generating audio...")
            await communicate.save(audio_file)
            
            file_size = os.path.getsize(audio_file) / 1024 / 1024
            print(f"✅ AUDIOBOOK CREATED: {audio_file}")
            print(f"📊 File size: {file_size:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Audio error: {e}")
            return False
    
    def create_report(self, base_name):
        """Create summary report"""
        print(f"\n📊 CREATING REPORTS...")
        
        report_file = os.path.join(self.output_dir, "reports", f"{base_name}_SUMMARY.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("AUDIOBOOK GENERATION SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Status: COMPLETED\n\n")
            f.write("GENERATED FILES:\n")
            f.write("• extracted/ - Original extracted text\n")
            f.write("• enriched/  - Processed enriched text\n")
            f.write("• audio/     - Audiobook MP3 file\n")
            f.write("• reports/   - This summary file\n")
        
        print(f"✅ REPORT CREATED: {report_file}")
    
    def show_results(self, base_name):
        """Show all generated files"""
        print(f"\n🎉 FINAL RESULTS FOR: {base_name}")
        print("=" * 50)
        
        print("📂 ALL GENERATED FILES:")
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                if base_name in file:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, ".")
                    size_kb = os.path.getsize(full_path) / 1024
                    print(f"   ✅ {relative_path} ({size_kb:.1f} KB)")
    
    def process(self, pdf_path):
        """Main processing function"""
        print("🚀 STARTING AUDIOBOOK MASTER PROCESS")
        print("=" * 60)
        
        # Step 1: Extract text
        extracted_text, base_name = self.extract_and_save_text(pdf_path)
        if not extracted_text:
            return False
        
        # Step 2: Enrich text  
        enriched_text = self.enrich_and_save_text(extracted_text, base_name)
        if not enriched_text:
            return False
        
        # Step 3: Create audio
        audio_success = asyncio.run(self.create_audio(enriched_text, base_name))
        
        # Step 4: Create report
        self.create_report(base_name)
        
        # Step 5: Show results
        self.show_results(base_name)
        
        print("\n" + "=" * 60)
        if audio_success:
            print("🎊 PROCESS COMPLETED SUCCESSFULLY!")
            print("📁 Check 'output_files' folder for all generated files!")
        else:
            print("⚠ PROCESS COMPLETED WITH AUDIO ISSUES")
            print("📁 Text files were generated successfully!")
        
        print("=" * 60)
        return audio_success

# Main execution
if __name__ == "__main__":
    print("AUDIOBOOK MASTER - Complete Pipeline")
    print("This will generate: EXTRACTED text + ENRICHED text + AUDIO")
    print()
    
    # Initialize the master
    master = AudiobookMaster(
        voice="en-US-AriaNeural",
        rate="+0%"
    )
    
    # Define PDF path
    pdf_file = "input_files/sample.pdf"
    
    # Check if PDF exists
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        print("\nPlease make sure:")
        print("1. There's an 'input_files' folder in current directory")
        print("2. There's a PDF file named 'sample.pdf' in it")
        print("3. Or update the pdf_file variable in the code")
        
        # Show current directory
        print(f"\n📂 Current directory contents:")
        for item in os.listdir('.'):
            if os.path.isdir(item):
                print(f"   📁 {item}/")
            else:
                print(f"   📄 {item}")
    else:
        # Run the complete process
        success = master.process(pdf_file)
        
        if success:
            print("\n✨ ALL OUTPUTS GENERATED SUCCESSFULLY!")
            print("🎵 Your complete audiobook package is ready!")
        else:
            print("\n💥 PROCESS COMPLETED WITH ERRORS")
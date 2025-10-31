import os
import fitz
from audiobook_generator import AudiobookGenerator

print("🎧 PDF AUDIOBOOK MAKER")
print("=" * 50)

# Check for PDF
pdf_path = "../input_files/book.pdf"

if not os.path.exists(pdf_path):
    print("❌ book.pdf not found in input_files folder!")
    input("Press Enter to exit...")
    exit()

print("📄 Processing: book.pdf")

# Extract text from PDF
doc = fitz.open(pdf_path)
text = ""

print("📖 Extracting text from PDF...")
for i in range(len(doc)):
    page = doc.load_page(i)
    page_text = page.get_text().strip()
    if page_text:
        text += page_text + "\n"
        print(f"  ✓ Page {i+1}: {len(page_text)} characters")

doc.close()

print(f"📊 Total text extracted: {len(text)} characters")

if not text.strip():
    print("❌ No text found in PDF!")
    input("Press Enter to exit...")
    exit()

# Show text preview
print(f"📄 First 300 characters:\n{text[:300]}...\n")

# Generate audiobook
print("🎧 Generating audiobook...")
generator = AudiobookGenerator()

# For long texts, use the first part for testing
if len(text) > 10000:
    print("📚 Long PDF detected - using first 10,000 characters for test")
    text_to_convert = text[:10000]
else:
    text_to_convert = text

output_file = "book_audiobook.mp3"
result = generator.generate_online(text_to_convert, output_file)

if result:
    print(f"✅ SUCCESS! Audiobook created: {output_file}")
    
    # Show file info
    file_size = os.path.getsize(output_file) / 1024
    print(f"📊 File size: {file_size:.1f} KB")
    
    play = input("\n🎵 Play the audiobook? (y/n): ").lower()
    if play == 'y':
        generator.play_audio(output_file)
else:
    print("❌ Failed to create audiobook")

print("\n🎉 Done!")
input("Press Enter to close...")

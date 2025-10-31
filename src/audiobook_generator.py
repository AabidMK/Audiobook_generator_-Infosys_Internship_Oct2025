from gtts import gTTS
import os
import subprocess

class AudiobookGenerator:
    def _init_(self):
        pass
    
    def generate_online(self, text, filename):
        """Generate high-quality speech using Google TTS"""
        try:
            # Ensure filename has a proper path
            if not filename:
                filename = "output_audiobook.mp3"
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Created directory: {directory}")
            
            # Split long text into chunks
            if len(text) > 4000:
                print("📖 Long text detected - splitting into chunks...")
                return self._generate_long_audio(text, filename)
            
            print(f"🎧 Generating audio: {os.path.basename(filename)}")
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filename)
            print(f"✅ High-quality audio saved: {filename}")
            
            # Show file size
            file_size = os.path.getsize(filename) / 1024  # KB
            print(f"📊 File size: {file_size:.1f} KB")
            
            return filename
            
        except Exception as e:
            print(f"❌ Google TTS failed: {e}")
            return None
    
    def _generate_long_audio(self, text, filename):
        """Generate audio for long texts by splitting into chunks"""
        # Split text into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < 4000:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        print(f"✓ Split into {len(chunks)} chunks")
        
        # Generate audio for each chunk
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_file = f"temp_chunk_{i+1}.mp3"
            try:
                print(f"  🎧 Generating chunk {i+1}/{len(chunks)}...")
                tts = gTTS(text=chunk, lang='en', slow=False)
                tts.save(temp_file)
                temp_files.append(temp_file)
                
                # Show chunk file size
                chunk_size = os.path.getsize(temp_file) / 1024
                print(f"    ✓ Saved: {temp_file} ({chunk_size:.1f} KB)")
                
            except Exception as e:
                print(f"    ❌ Failed chunk {i+1}: {e}")
        
        if temp_files:
            # Use first chunk as main output
            os.rename(temp_files[0], filename)
            print(f"✅ Main audio saved: {filename}")
            
            # Keep other chunks for reference
            for temp_file in temp_files[1:]:
                if os.path.exists(temp_file):
                    print(f"📁 Additional chunk: {temp_file}")
            
            return filename
        else:
            return None
    
    def play_audio(self, filename):
        """Play audio using system default player"""
        try:
            if os.path.exists(filename):
                os.startfile(filename)
                print(f"▶ Playing: {filename}")
            else:
                print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Playback failed: {e}")

def main():
    print("🎧 AUDIOBOOK GENERATOR (Google TTS Only)")
    print("=" * 50)
    
    generator = AudiobookGenerator()
    
    # Test with sample text
    test_text = "Hello! This is a test of the audiobook generator using Google Text to Speech. The audio quality should be high and natural sounding. This system is now working properly without any path errors."
    
    output_file = "test_audiobook.mp3"  # Simple filename in current directory
    
    print("🔄 Generating audiobook...")
    result = generator.generate_online(test_text, output_file)
    
    if result:
        print(f"✅ Success! Audio saved: {output_file}")
        
        play = input("🎵 Play the audio? (y/n): ").lower()
        if play == 'y':
            generator.play_audio(output_file)
    else:
        print("❌ Failed to generate audio")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
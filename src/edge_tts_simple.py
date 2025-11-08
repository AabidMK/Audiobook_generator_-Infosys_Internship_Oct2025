import os
import asyncio
import edge_tts

class EdgeTTSSimple:
    def __init__(self, voice="en-US-AriaNeural"):
        self.voice = voice
    
    async def generate_audio_async(self, text, output_file):
        """Generate audio using Edge TTS without combining"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            print(f"🎧 Generating audio with Edge TTS (Voice: {self.voice})...")
            
            # For long texts, split and use first part
            if len(text) > 10000:
                print("📚 Long text detected - using first 10,000 characters")
                text = text[:10000]
            
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_file)
            
            print(f"✅ Edge TTS audio saved: {output_file}")
            
            # Show file info
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / 1024
                print(f"📊 File size: {file_size:.1f} KB")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Edge TTS error: {e}")
            return None
    
    def generate_audio(self, text, output_file):
        """Synchronous wrapper for async method"""
        return asyncio.run(self.generate_audio_async(text, output_file))
    
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
    print("🎧 EDGE TTS SIMPLE GENERATOR")
    print("=" * 50)
    
    # Available voices
    voices = [
        "en-US-AriaNeural",      # Female, expressive
        "en-US-JennyNeural",     # Female, friendly  
        "en-GB-SoniaNeural",     # British female
        "en-US-GuyNeural",       # Male, confident
    ]
    
    print("Available voices:")
    for i, voice in enumerate(voices, 1):
        print(f"  {i}. {voice}")
    
    try:
        choice = int(input(f"\nSelect voice (1-{len(voices)}): "))
        selected_voice = voices[choice-1]
        
        generator = EdgeTTSSimple(voice=selected_voice)
        
        # Test text
        test_text = """
        Hello! This is a test of Microsoft Edge TTS. 
        This service uses high-quality neural voices and is completely free to use.
        The audio quality is excellent and sounds very natural.
        You can use this for your audiobook project without any costs.
        """
        
        output_file = "edge_tts_simple_test.mp3"
        
        print(f"\n🔄 Generating audio with voice: {selected_voice}")
        result = generator.generate_audio(test_text, output_file)
        
        if result:
            print(f"✅ Success! Audio saved: {output_file}")
            
            play = input("\n🎵 Play the audio? (y/n): ").lower()
            if play == 'y':
                generator.play_audio(output_file)
        else:
            print("❌ Failed to generate audio")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
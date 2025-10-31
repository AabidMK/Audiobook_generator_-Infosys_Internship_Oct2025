import os
import tempfile
import subprocess
import sys

def text_to_speech(text, rate=150, out_format='wav'):
    """Converts text to speech and returns path to audio file."""
    print(f"Starting text-to-speech conversion...")
    print(f"Text: '{text}'")
    print(f"Rate: {rate}, Format: {out_format}")
    
    try:
        import pyttsx3
        print("✓ pyttsx3 imported successfully")
    except Exception as e:
        print(f"✗ pyttsx3 not available: {e}")
        # if pyttsx3 not available, write text to a .txt and return that path for debugging
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        tmp.write(text.encode('utf-8'))
        tmp.close()
        print(f"Created text file instead: {tmp.name}")
        return tmp.name

    try:
        engine = pyttsx3.init()
        print("✓ pyttsx3 engine initialized")
        
        # Set rate
        engine.setProperty('rate', rate)
        print(f"✓ Speech rate set to: {rate}")
        
        # Try to set a voice if available
        voices = engine.getProperty('voices')
        print(f"✓ Found {len(voices)} available voices")
        for i, voice in enumerate(voices):
            print(f"  Voice {i}: {voice.name}")
        
        if voices:
            try:
                engine.setProperty('voice', voices[0].id)
                print(f"✓ Voice set to: {voices[0].name}")
            except Exception as e:
                print(f"✗ Could not set voice: {e}")

        # Create output file
        out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        out_path = out_file.name
        out_file.close()
        print(f"✓ Temporary file created: {out_path}")

        # Save to file using pyttsx3's save_to_file
        print("Saving speech to file...")
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        print("✓ Speech generated successfully")

        # Check if file was created
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            file_size = os.path.getsize(out_path)
            print(f"✓ Audio file created: {out_path} ({file_size} bytes)")
            return out_path
        else:
            print(f"✗ Audio file creation failed: {out_path}")
            return None

    except Exception as e:
        print(f"✗ Error during text-to-speech conversion: {e}")
        return None

def play_audio(file_path):
    """Try to play audio using system default player"""
    try:
        if sys.platform == "win32":
            # Windows
            os.startfile(file_path)
        elif sys.platform == "darwin":
            # macOS
            subprocess.run(["afplay", file_path])
        else:
            # Linux
            subprocess.run(["aplay", file_path])
        print(f"✓ Playing audio file: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Could not play audio: {e}")
        print(f"✓ Audio file saved at: {file_path}")
        return False

# Example usage
if __name__ == "__main__":
    print("=" * 50)
    print("TEXT-TO-SPEECH TEST")
    print("=" * 50)
    
    # Test the function
    test_text = "Hello, this is Saubhagya Mishra and this is a text to speech test! How are you today?"
    audio_file = text_to_speech(test_text, rate=150, out_format='wav')
    
    print("\n" + "=" * 50)
    if audio_file and os.path.exists(audio_file):
        print(f"SUCCESS: Audio file created at: {audio_file}")
        file_size = os.path.getsize(audio_file)
        print(f"File size: {file_size} bytes")
        
        # Try to play the audio
        print("\nAttempting to play audio...")
        play_audio(audio_file)
    else:
        print("ERROR: Text-to-speech conversion failed")
    
    print("=" * 50)
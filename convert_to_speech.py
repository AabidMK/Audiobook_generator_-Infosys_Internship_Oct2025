"""
Standalone script to convert enriched text files to speech
"""

import sys
from pathlib import Path
from tts_converter import TTSConverter


def main():
    """Main function to convert text to speech"""
    
    if len(sys.argv) < 2:
        print("Usage: python convert_to_speech.py <text_file_path> [--voice <voice_name>]")
        print("Example: python convert_to_speech.py enriched_texts/document_enriched.txt")
        print("Example: python convert_to_speech.py enriched_texts/document_enriched.txt --voice en-US-AriaNeural")
        sys.exit(1)
    
    text_file_path = sys.argv[1]
    
    # Check for voice argument
    voice = None
    if '--voice' in sys.argv:
        idx = sys.argv.index('--voice')
        if idx + 1 < len(sys.argv):
            voice = sys.argv[idx + 1]
    
    try:
        print("=" * 50)
        print("TEXT-TO-SPEECH CONVERSION")
        print("=" * 50)
        
        converter = TTSConverter(output_folder="audio_output")
        
        text_length = len(open(text_file_path, 'r', encoding='utf-8').read())
        
        print(f"File: {text_file_path}")
        print(f"Text length: {text_length:,} characters")
        
        # Convert to speech (automatically handles long texts by combining into single file)
        output_path = converter.convert_file(text_file_path, voice=voice)
        
        print("\n" + "=" * 50)
        print("CONVERSION COMPLETE")
        print("=" * 50)
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✅ Audio file saved to: {output_path}")
        print(f"File size: {file_size_mb:.2f} MB")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


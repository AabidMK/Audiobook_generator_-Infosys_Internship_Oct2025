"""
Main orchestrator for audiobook generator
Processes files through text extraction and enrichment
"""

import sys
from pathlib import Path
from pipeline import AudiobookPipeline


def main():
    """Main function to process files"""
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <file_path> [--api-key <gemini_api_key>] [--tts]")
        print("Example: python main.py document.pdf")
        print("Example: python main.py document.pdf --api-key YOUR_API_KEY --tts")
        print("\nOptions:")
        print("  --api-key    Google Gemini API key (or set GEMINI_API_KEY env var)")
        print("  --tts        Convert enriched text to speech (audio output)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check for API key argument
    api_key = None
    if '--api-key' in sys.argv:
        idx = sys.argv.index('--api-key')
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]
    
    # Check for TTS flag
    enable_tts = '--tts' in sys.argv
    
    pipeline = AudiobookPipeline()

    try:
        pipeline.process(
            file_path,
            api_key=api_key,
            convert_to_audio=enable_tts,
            verbose=True,
        )
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


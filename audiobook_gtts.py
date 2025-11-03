from gtts import gTTS
import os

def text_to_speech_gtts(input_file, output_file, lang='en', slow=False):
    """
    Converts a text file into an audio file using Google Text-to-Speech (gTTS).

    Parameters:
        input_file (str): Path to the text file containing the text to convert.
        output_file (str): Path where the generated .mp3 file will be saved.
        lang (str): Language code (default 'en' for English).
        slow (bool): If True, speech will be slower and clearer.
    """
    try:
        # Read text content
        with open(input_file, "r", encoding="utf-8") as file:
            text = file.read().strip()

        # Skip empty files
        if not text:
            print(f"⚠️ Skipped empty file: {input_file}")
            return

        # Generate speech
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(output_file)
        print(f"✅ Audio saved: {output_file}")

    except Exception as e:
        print(f"❌ Error processing {input_file}: {e}")


if __name__ == "__main__":
    # Directory setup
    input_dir = "."
    output_dir = "."
    os.makedirs(output_dir, exist_ok=True)

    # List of text files to convert (adjust names if needed)
    text_files = [
        "sample1_enriched_output.txt",
        "sample2_enriched_output.txt",
        "sample3_enriched_output.txt",
        "sample4_enriched_output.txt"
    ]

    # Convert each text file to audio
    for text_file in text_files:
        input_path = os.path.join(input_dir, text_file)
        output_path = os.path.join(output_dir, text_file.replace("_enriched_output.txt", "_audio.mp3"))

        print(f"\nConverting {text_file} -> {os.path.basename(output_path)}")
        text_to_speech_gtts(input_path, output_path)

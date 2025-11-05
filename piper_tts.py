import os
import base64
import re
import wave 
import io
from piper.voice import PiperVoice
from dotenv import load_dotenv 

load_dotenv()

# --- IMPORTANT ---
# Set your downloaded model file here.
# It MUST be in the same folder as this script.
MODEL_FILE = "en_US-lessac-medium.onnx"
# -----------------

# --- Global Model Loading ---
# We load the model once when the script starts.
try:
    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")
    
    print(f"Loading Piper TTS model from {MODEL_FILE}...")
    model = PiperVoice.load(MODEL_FILE)
    # Adjust length_scale to medium pace (1.5 = slightly slower than normal for pleasant listening)
    model.config.length_scale = 1.5
    print("✅ Piper TTS model loaded successfully.")
    
    # Get the model's native sample rate
    MODEL_SAMPLE_RATE = model.config.sample_rate
    # Define the MIME type, just like the original file, to pass the sample rate
    MODEL_MIME_TYPE = f"audio/L16;rate={MODEL_SAMPLE_RATE}"
    
except Exception as e:
    print(f"❌ Failed to load Piper model: {e}")
    print("Please make sure 'pip install piper-tts' is complete and")
    print(f"the model file '{MODEL_FILE}' and its .json file are in the correct directory.")
    model = None
# ----------------------------

def generate_tts(text_to_speak):
    """
    Calls the *local* Piper model to generate speech from text.
    Returns the base64-encoded audio data and its MIME type.

    This function has the *exact same interface* as the tts_google.py version.
    """
    if model is None:
        print("❌ Cannot generate TTS: Piper model is not loaded.")
        return None, None

    print("Sending text to local Piper model...")

    try:
        # 1. Synthesize audio into chunks
        chunks = list(model.synthesize(text_to_speak))

        if not chunks:
            print("Error: Piper generated no audio chunks.")
            return None, None

        # 2. Combine all audio chunks into a single byte array
        pcm_data = b''.join(chunk.audio_int16_bytes for chunk in chunks)

        # 3. Encode the raw bytes as base64 (as a string)
        audio_data = base64.b64encode(pcm_data).decode('utf-8')

        if audio_data:
            print("Speech generated successfully.")
            return audio_data, MODEL_MIME_TYPE
        else:
            print("Error: Piper generated empty audio data.")
            return None, None

    except Exception as e:
        print(f"❌ An unexpected error occurred during Piper generation: {e}")
        return None, None

def save_audio_to_wav(base64_audio_data, mime_type, filename="output.wav"):
    """
    Decodes the Base64 audio data and saves it as a WAV file.

    *** This function is IDENTICAL to the one from tts_google.py ***
    It works perfectly because generate_tts() provides the exact same
    data format (base64-encoded L16 PCM).
    """
    print(f"Saving audio to {filename}...")

    try:
        # Extract sample rate from the mime type string
        sample_rate_match = re.search(r'rate=(\d+)', mime_type)
        sample_rate = int(sample_rate_match.group(1)) if sample_rate_match else 22050 # Default

        # Decode the base64 data to raw PCM bytes
        pcm_data = base64.b64decode(base64_audio_data)

        # Define audio parameters for the WAV file
        # Get from the first chunk since all chunks have the same format
        chunks = list(model.synthesize("test"))
        if chunks:
            num_channels = chunks[0].sample_channels
            bytes_per_sample = chunks[0].sample_width
        else:
            num_channels = 1
            bytes_per_sample = 2  # 16-bit audio

        # Write the PCM data to a WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(bytes_per_sample)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)

        print(f"\nSuccessfully saved speech to '{filename}'.")
        print("You can now play this file using any media player.")

    except Exception as e:
        print(f"❌ Error saving WAV file: {e}")

def generate_and_save_audio(text_to_speak, output_filename="output.wav"):
    """
    Generates speech from text and saves it directly to a file.
    This is the function that main.py expects to import.
    """
    if model is None:
        print("❌ Cannot generate audio: TTS model was not loaded.")
        return False

    try:
        print(f"\nGenerating audio and saving to {output_filename}...")
        audio_data, mime_type = generate_tts(text_to_speak)

        if audio_data and mime_type:
            save_audio_to_wav(audio_data, mime_type, output_filename)
            return True
        else:
            print("❌ TTS generation failed.")
            return False

    except Exception as e:
        print(f"❌ Error during Piper TTS generation: {e}")
        return False

# This test block only runs when you execute `python piper_tts.py`
if __name__ == "__main__":
    print("\n--- Running a standalone test of piper_tts.py ---")
    SAMPLE_TEXT = "Hello! This is a test of the local Piper TTS model."
    
    if model:
        audio_data, mime_type = generate_tts(SAMPLE_TEXT)
        if audio_data and mime_type:
            save_audio_to_wav(audio_data, mime_type, "piper_test_output.wav")
    else:
        print("Test failed: Model not loaded.")

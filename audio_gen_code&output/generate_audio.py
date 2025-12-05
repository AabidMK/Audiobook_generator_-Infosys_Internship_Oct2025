import asyncio
import os
import tkinter as tk
from tkinter import filedialog
import edge_tts


VOICE_TO_USE = "en-US-AndrewNeural" 
OUTPUT_FILENAME_BASE = "Audiobook_Part"


async def generate_audiobook_segment(text_content, segment_number):
    """Generates an MP3 file from a text chunk using Edge TTS."""
    
    
    output_file = f"{OUTPUT_FILENAME_BASE}_{segment_number:02d}.mp3"

    
    ssml_text = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{VOICE_TO_USE}">
            <prosody rate="+5%">
                <break time="100ms"/>
                {text_content}
            </prosody>
        </voice>
    </speak>
    """
    
    
    communicate = edge_tts.Communicate(ssml_text, VOICE_TO_USE)
    await communicate.save(output_file)
    
    print(f"✅ Success: Saved audio segment to '{output_file}'")
    return output_file

def main_tts_pipeline():
    
    print("A file selection window will pop up. Select your ENRICHED .txt file.")
    root = tk.Tk()
    root.withdraw() 
    
    input_file_path = filedialog.askopenfilename(
        title="Select the ENRICHED Script .txt File (Module 2 Output)",
        filetypes=[("Text files", "*.txt")]
    )

    if not input_file_path:
        print("No file selected. Exiting script.")
        return

    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            enriched_text = f.read()
        print(f"Reading input file: {input_file_path}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    
    text_chunks = [chunk.strip() for chunk in enriched_text.split('\n\n\n\n') if chunk.strip()]
    
    if not text_chunks:
        print("Error: Text file is empty or cannot be split correctly.")
        return
        
    print(f"Found {len(text_chunks)} segments to convert.")
    
   
    output_files = []
    
    
    os.chdir(os.path.dirname(input_file_path))

    
    loop = asyncio.get_event_loop_policy().get_event_loop()
    
    try:
        for i, chunk in enumerate(text_chunks):
            print(f"--- Generating Segment {i+1} of {len(text_chunks)} ---")
             
            output_file = loop.run_until_complete(generate_audiobook_segment(chunk, i + 1))
            output_files.append(output_file)
    except Exception as e:
        print(f"\nFATAL TTS ERROR: {e}")
        print("Audio generation failed for one or more segments. Check your text for strange characters.")
    finally:
        
        if loop.is_running():
            loop.close()

    print("\n\n✅ ALL AUDIO GENERATION COMPLETE!")
    print(f"Total files created: {len(output_files)}. They are saved in the input file's directory.")


if __name__ == "__main__":
    main_tts_pipeline()
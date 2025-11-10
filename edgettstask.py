import asyncio
import os
from pathlib import Path

async def save_tts_edge_async(text, output_path, filename, voice='en-US-AriaNeural'):
    """
    Convert text to speech using Edge TTS and save as MP3
    
    Args:
        text (str): Your enriched text
        output_path (str): Folder path to save the file
        filename (str): Name without extension
        voice (str): Voice model to use
    """
    print("🎙️ Converting text to speech using Microsoft Edge TTS...")
    print(f"Text length: {len(text)} characters")
    print(f"Voice: {voice}")
    
    try:
        import edge_tts
        
        # Create output directory
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Create full file path
        full_path = os.path.join(output_path, f"{filename}.mp3")
        
        # Create communicate object and save
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(full_path)
        
        # Verify file
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"✅ SUCCESS: Audio file saved!")
            print(f"📁 Location: {full_path}")
            print(f"📊 File size: {file_size:,} bytes")
            return full_path
        else:
            print("❌ ERROR: File was not created")
            return None
            
    except Exception as e:
        print(f"❌ Error with Edge TTS: {e}")
        return None

def save_tts_edge(text, output_path, filename, voice='en-US-AriaNeural'):
    """Wrapper for async function"""
    return asyncio.run(save_tts_edge_async(text, output_path, filename, voice))

def list_available_voices():
    """Display available English voices"""
    async def list_voices_async():
        try:
            import edge_tts
            voices = await edge_tts.VoicesManager.create()
            english_voices = [v for v in voices if 'en' in v['Locale']]
            
            print("🎭 Available English Voices:")
            for i, voice in enumerate(english_voices[:10]):  # Show first 10
                print(f"  {i+1}. {voice['ShortName']} - {voice['Gender']} - {voice['Locale']}")
            print("  ... and more!")
            
        except Exception as e:
            print(f"Error listing voices: {e}")
    
    asyncio.run(list_voices_async())

# Example usage
if __name__ == "__main__":
    # Your enriched text here
    my_enriched_text = """
    Here's an enhanced version of the assignment, focusing on improved clarity, readability, and structure while maintaining academic integrity:

**Computer Organization and Architecture (KCS-302)**
**Assignment: Unit 5 – Input/Output Organization**

**Course Outcome (CO) Addressed:** CO5 (Relating to Input/Output Organization)

**Instructions:**  Answer the following questions thoroughly.  Each question is associated with a Bloom's Taxonomy level (indicated in parentheses), reflecting the cognitive skill being assessed. Questions also indicate which academic years they were previously used.

| S. No. | Question                                                                                                                                                                                             | CO/Bloom's Level | Previous Academic Years |
|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|--------------------------|
| 1     | Define and explain the concept of a vector interrupt.                                                                                                                                                 | CO5 / K2 (Understanding) | 2020-21                  |
| 2     | Briefly describe Reduced Instruction Set Computing (RISC) architecture.                                                                                                                              | CO3 / K2 (Understanding) | 2017-18, 2020-21           |
| 3     | Explain the term "cycle stealing" in the context of Direct Memory Access (DMA).                                                                                                                        | CO5 / K2 (Understanding) | 2018-19, 2020-21           |
| 4     | Differentiate between daisy chaining and centralized parallel arbitration techniques for bus arbitration.                                                                                            | CO5 / K2 (Understanding) | 2018-19, 2021-22           |
| 5     | Calculate the data transfer rate of an eight-track magnetic tape with a speed of 120 inches per second and a density of 1600 bits per inch. Show your workings.                                      | CO5 / K3 (Applying)    | 2021-22                  |
| 6     | Define the term "I/O control method."                                                                                                                                                                  | CO5 / K1 (Remembering)   | 2019-20                  |
| 7     | Define the term "Bus Arbitration."                                                                                                                                                                     | CO5 / K2 (Understanding) | 2019-20                  |
| 8     | a. Discuss the design considerations for a typical input/output interface.                                                                                                                        | CO5 / K2 (Understanding) | 2019-20                  |
|       | b. Define the concept of interrupts. Explain how interrupts are typically handled by a computer system.                                                                                           | CO5 / K2 (Understanding) | 2019-20                  |
| 9     | Explain the difference between vectored and non-vectored interrupts, providing a specific example of each.                                                                                           | CO5 / K2 (Understanding) | 2018-19                  |
| 10    | Explain each of the phases involved in a typical instruction cycle.                                                                                                                                   | CO5 / K2 (Understanding) | 2018-19                  |
| 11    | Explain why the read and write lines in a DMA controller are bidirectional.                                                                                                                             | CO5 / K2 (Understanding) | 2018-19                  |
| 12    | Compare and contrast isolated I/O and memory-mapped I/O. Include a discussion of the advantages and disadvantages of each approach.                                                                | CO5 / K2 (Understanding) | 2019-20                  |
| 13    | a. Draw a block diagram of a typical DMA controller and explain the function of each component.                                                                                                   | CO5 / K2 (Understanding) | 2018-19, 2019-20, 2020-21 |
|       | b. Describe how DMA is used to transfer data from peripheral devices to memory.                                                                                                                     | CO5 / K2 (Understanding) | 2018-19, 2019-20, 2020-21 |
| 14    | Define asynchronous data transfer. Explain both strobe control and handshaking mechanisms used for asynchronous data transfer.                                                                     | CO5 / K2 (Understanding) | 2020-21, 2021-22           |
| 15    | Discuss the different modes of data transfer (e.g., programmed I/O, interrupt-driven I/O, DMA).                                                                                                       | CO5 / K1 (Remembering)   | 2020-21                  |
| 16    | Explain how computer buses can be used for communication between the CPU, memory, and I/O devices. Include a block diagram illustrating CPU-IOP (Input/Output Processor) communication.                  | CO5 / K2 (Understanding) | 2021-22                  |

**Prepared By:** Sanjay Goswami
**Department:** CSE
**Institution:** UCER-Prayagraj
**Revised version Highlights**

*   **Clearer Introduction:** Added a brief introductory paragraph outlining the assignment's scope and purpose.
*   **Table Format:**  Organized the questions into a table for enhanced readability and structure.
*   **Explicit Instructions:** Included instructions on how to answer the questions (thoroughly).
*   **Bloom's Taxonomy Clarification:** Specified that the Bloom's level refers to the cognitive skill being assessed.
*   **Precise Wording:** Modified question wording for improved clarity and conciseness (e.g., using "Define and explain" instead of "What do you mean by").
*   **Consistent Terminology:** Ensured consistent use of terminology (e.g., "Direct Memory Access (DMA)" used in full at first instance).
*   **Removal of Redundancy:** Eliminated repetitive phrases and information already present in the table headings.
*   **Improved Flow:**  Rearranged some wording to improve the overall flow of the assignment.
*   **Combined Related Questions:**  Combined related questions into multi-part questions (e.g., Question 8 and Question 13). This makes for a more logical structure.
*   **Formatting:** Improved formatting for visual appeal.
*   **Proper Heading:** added proper heading to assignment, including name of course and a brief description
*   **Revised Footnote:** Removed footnote with page number

This revised version is more user-friendly for students while retaining the original academic rigor and information. It is also easier for the instructor to manage and assess.
    """
    
    # Specify your save location
    save_folder = r"C:\Users\hp\Desktop\SM\infy internship"  # Change this path!
    file_name = "edge_tts_audiobook"
    
    # List available voices (uncomment to see options)
    # list_available_voices()
    
    # Popular voice options:
    voices = [
        'en-US-AriaNeural',      # Female - Very natural
        'en-US-DavisNeural',     # Male - Professional
        'en-US-JennyNeural',     # Female - Friendly
        'en-GB-SoniaNeural',     # British Female - Elegant
    ]
    
    # Convert and save
    audio_file = save_tts_edge(
        text=my_enriched_text,
        output_path=save_folder,
        filename=file_name,
        voice=voices[0]  # Using Aria voice
    )
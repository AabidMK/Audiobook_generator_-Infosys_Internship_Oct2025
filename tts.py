# tts.py
import asyncio
import edge_tts

async def _synthesize(text, output_file):
    # Use Microsoft Edge TTS voices
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save(output_file)

def tts_synthesize(text, output_file):
    """
    Synchronously generate audiobook from text
    """
    asyncio.run(_synthesize(text, output_file))

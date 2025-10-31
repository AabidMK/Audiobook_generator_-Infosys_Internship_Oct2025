"""
Simple Bark TTS Test - Short sentence only
"""
from tts import tts_synthesize
import os

print("🎙️ Testing Bark TTS with a very short sentence...")
print("Note: This will be slow (5-10 seconds) and may fail due to PyTorch compatibility.\n")

# Very short test text
test_text = "Hello, this is a test."

print(f"Text: '{test_text}'")
print("\n⏳ Generating audio with Bark...")
print("(First time will download 2-10GB of models)\n")

try:
    output = tts_synthesize(
        text=test_text,
        engine="bark",
        basename="bark_short_test"
    )
    print(f"\n✅ Success! Audio saved to: {output}")
    print(f"File size: {output.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"\n❌ Bark failed: {e}")
    print("\n💡 Recommendation: Use gTTS or Edge-TTS instead for reliable results.")

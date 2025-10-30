"""
Test Bark TTS integration
"""
from tts import tts_synthesize, list_available_engines

# Check if Bark is available
print("Available TTS Engines:")
print("=" * 50)
for name, info in list_available_engines().items():
    status = "✓" if info["available"] else "✗"
    print(f"{status} {name:12} | Quality: {info['quality']:20} | {info['notes']}")
print("=" * 50)

# Test Bark with a short sentence
test_text = "Hello! This is a test of the Bark text to speech engine."

print("\n🎙️ Testing Bark TTS...")
print(f"Text: {test_text}")
print("\nNote: First run will download 2-10GB of models. This may take several minutes.")
print("Generation is also slow (5-10 seconds per sentence).\n")

try:
    output_path = tts_synthesize(
        text=test_text,
        engine="bark",
        basename="bark_test"
    )
    print(f"✅ Success! Audio saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")
except Exception as e:
    print(f"❌ Error: {e}")

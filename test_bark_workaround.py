"""
Bark TTS Test with PyTorch workaround
"""
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

import torch
# Disable weights_only for Bark compatibility
torch.serialization.DEFAULT_STRICT_WEIGHTS_ONLY = False

print("🎙️ Testing Bark TTS with PyTorch workaround...")
print("This will be VERY slow (2-3 minutes for a short sentence)\n")

try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    import scipy.io.wavfile as wavfile
    from pathlib import Path
    
    # Very short test
    text = "Hello, this is Bark."
    
    print(f"Text: '{text}'")
    print("\n⏳ Loading Bark models (first time downloads 2-10GB)...")
    
    preload_models()
    
    print("⏳ Generating audio (this takes 30-60 seconds)...")
    audio_array = generate_audio(text)
    
    output_path = Path("outputs/audio/bark_test.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    wavfile.write(str(output_path), SAMPLE_RATE, audio_array)
    
    print(f"\n✅ Success! Audio saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    
except Exception as e:
    print(f"\n❌ Bark failed: {type(e).__name__}: {e}")
    print("\n💡 Bark requires PyTorch 2.0.1 or older")
    print("   Current PyTorch 2.9 has compatibility issues")
    print("\n✅ Recommendation: Use Edge-TTS instead (best quality & fast!)")

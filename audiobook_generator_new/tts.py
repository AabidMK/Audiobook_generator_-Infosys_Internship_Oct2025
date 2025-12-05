import os, tempfile
def text_to_speech(text, rate=150, out_format='mp3'):
    """Converts text to speech and returns path to audio file.
    Uses pyttsx3 for offline synthesis by default. Produces WAV then optionally converts to MP3 if requested
    (conversion to MP3 is not implemented here to avoid external deps; the file will be WAV if mp3 not supported).
    """
    try:
        import pyttsx3
    except Exception as e:
        # if pyttsx3 not available, write text to a .txt and return that path for debugging
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        tmp.write(text.encode('utf-8'))
        tmp.close()
        return tmp.name

    engine = pyttsx3.init()
    # Set rate
    engine.setProperty('rate', rate)
    # Try to set a voice if available (leave default otherwise)
    voices = engine.getProperty('voices')
    if voices:
        try:
            engine.setProperty('voice', voices[0].id)
        except Exception:
            pass

    out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    out_path = out_file.name
    out_file.close()

    # Save to file using pyttsx3's save_to_file
    engine.save_to_file(text, out_path)
    engine.runAndWait()

    # If user requested mp3, keep wav but change extension in name for consistency (no conversion)
    if out_format == 'mp3':
        mp3_path = out_path[:-4] + '.mp3'
        try:
            # Attempt to convert with pydub if available
            from pydub import AudioSegment
            AudioSegment.from_wav(out_path).export(mp3_path, format='mp3')
            return mp3_path
        except Exception:
            # Conversion not available; return WAV path
            return out_path
    return out_path

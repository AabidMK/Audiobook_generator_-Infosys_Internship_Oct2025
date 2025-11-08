import pyttsx3

class PyTTSX3Generator:
    def __init__(self, rate=150, volume=0.9, voice_index=0):
        self.engine = pyttsx3.init()
        self.set_rate(rate)
        self.set_volume(volume)
        self.set_voice(voice_index)
    
    def set_rate(self, rate):
        """Set speech rate"""
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume):
        """Set volume level (0.0 to 1.0)"""
        self.engine.setProperty('volume', volume)
    
    def set_voice(self, voice_index):
        """Set voice by index"""
        voices = self.engine.getProperty('voices')
        if voices and voice_index < len(voices):
            self.engine.setProperty('voice', voices[voice_index].id)
    
    def generate_audio(self, text, output_file):
        """Generate audio from text and save to file"""
        try:
            self.engine.save_to_file(text, output_file)
            self.engine.runAndWait()
            print(f"Audio saved to: {output_file}")
            return True
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
    
    def stop(self):
        """Stop the engine"""
        self.engine.stop()
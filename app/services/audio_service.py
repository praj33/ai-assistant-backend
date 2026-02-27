import io
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class AudioService:
    def __init__(self):
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
    
    def text_to_speech(self, text: str, language: str = "en", output_format: str = "mp3") -> bytes:
        """
        Convert text to speech and return audio bytes
        """
        if not GTTS_AVAILABLE:
            print("gTTS not available, audio output disabled")
            return b""
        
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_bytes = audio_buffer.getvalue()
            
            return audio_bytes
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            return b""
    
    def speech_to_text(self, audio_data: bytes, language: str = "en") -> str:
        """
        Convert speech (audio bytes) to text
        """
        if not PYDUB_AVAILABLE or not SR_AVAILABLE:
            print("Audio processing libraries not available")
            return ""
        
        try:
            # Save audio bytes to a temporary file for processing
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            temp_wav_path = "temp_audio.wav"
            audio_segment.export(temp_wav_path, format="wav")
            
            # Use speech recognition
            with sr.AudioFile(temp_wav_path) as source:
                audio = self.recognizer.record(source)
                
            try:
                text = self.recognizer.recognize_google(audio, language=language)
                return text
            except sr.UnknownValueError:
                return "Could not understand the audio"
            except sr.RequestError as e:
                return f"Error with speech recognition service: {str(e)}"
        except Exception as e:
            print(f"Error in speech-to-text: {str(e)}")
            return ""
    
    def validate_audio_format(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Validate audio format and return metadata
        """
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            return {
                "valid": True,
                "duration_ms": len(audio_segment),
                "sample_rate": audio_segment.frame_rate,
                "channels": audio_segment.channels,
                "format": audio_segment.format,
                "bit_depth": audio_segment.sample_width * 8
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def convert_audio_format(self, audio_data: bytes, target_format: str = "mp3") -> bytes:
        """
        Convert audio to a specific format
        """
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=target_format)
            return output_buffer.getvalue()
        except Exception as e:
            print(f"Error converting audio format: {str(e)}")
            return b""
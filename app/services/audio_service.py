"""
AudioService — Text-to-Speech and Speech-to-Text for Mitra AI

Uses Vaani XTTS engine (from mitra_tts_integration) as the TTS provider.
Includes speech-to-text via SpeechRecognition library.
"""

import io
import asyncio
import importlib.util
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AudioService")

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

def _has_optional_dependency(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


_XTTS_RUNTIME_READY = _has_optional_dependency("TTS") and _has_optional_dependency("torch")

# Import TTS provider from mitra_tts_integration only when optional runtime deps exist.
try:
    if _XTTS_RUNTIME_READY:
        from app.services.mitra_tts_integration.tts_provider import tts_provider
        XTTS_AVAILABLE = True
    else:
        raise ImportError("Optional XTTS runtime dependencies are not installed")
except Exception:
    XTTS_AVAILABLE = False
    tts_provider = None
    logger.warning("[AudioService] XTTS optional dependencies unavailable, TTS disabled")


class AudioService:
    def __init__(self):
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
        
        self._tts_provider = tts_provider if XTTS_AVAILABLE else None

    def text_to_speech(self, text: str, language: str = "en", output_format: str = "wav") -> bytes:
        """
        Convert text to speech using XTTS engine (synchronous wrapper).
        
        Args:
            text: Text to synthesize.
            language: ISO 639-1 language code.
            output_format: Output audio format (default: wav).
            
        Returns:
            bytes: Audio data.
        """
        if not self._tts_provider:
            logger.warning("[AudioService] TTS provider not available")
            return b""

        try:
            # Run the async generate_audio in a sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context — use a helper
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(self._sync_tts, text, language)
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(
                    self._tts_provider.generate_audio(text, language=language)
                ) or b""
        except Exception as e:
            logger.error(f"[AudioService] TTS failed: {e}")
            return b""

    async def text_to_speech_async(self, text: str, language: str = "en") -> bytes:
        """
        Convert text to speech using XTTS engine (async).
        
        Args:
            text: Text to synthesize.
            language: ISO 639-1 language code.
            
        Returns:
            bytes: WAV audio data.
        """
        if not self._tts_provider:
            logger.warning("[AudioService] TTS provider not available")
            return b""

        try:
            audio_bytes = await self._tts_provider.generate_audio(text, language=language)
            return audio_bytes or b""
        except Exception as e:
            logger.error(f"[AudioService] TTS failed: {e}")
            return b""

    def _sync_tts(self, text: str, language: str) -> bytes:
        """Helper to run async TTS in a new event loop (for sync callers)."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._tts_provider.generate_audio(text, language=language)
            ) or b""
        finally:
            loop.close()

    def speech_to_text(self, audio_data: bytes, language: str = "en") -> str:
        """
        Convert speech (audio bytes) to text using SpeechRecognition.
        """
        if not PYDUB_AVAILABLE or not SR_AVAILABLE:
            logger.warning("[AudioService] Audio processing libraries not available")
            return ""

        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            temp_wav_path = "temp_audio.wav"
            audio_segment.export(temp_wav_path, format="wav")

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
            logger.error(f"[AudioService] Speech-to-text failed: {e}")
            return ""

    def validate_audio_format(self, audio_data: bytes) -> Dict[str, Any]:
        """Validate audio format and return metadata."""
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            return {
                "valid": True,
                "duration_ms": len(audio_segment),
                "sample_rate": audio_segment.frame_rate,
                "channels": audio_segment.channels,
                "format": audio_segment.format,
                "bit_depth": audio_segment.sample_width * 8,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def convert_audio_format(self, audio_data: bytes, target_format: str = "mp3") -> bytes:
        """Convert audio to a specific format."""
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=target_format)
            return output_buffer.getvalue()
        except Exception as e:
            logger.error(f"[AudioService] Audio conversion failed: {e}")
            return b""

    def get_tts_status(self) -> Dict[str, Any]:
        """Return operational status of the TTS provider."""
        if self._tts_provider:
            return self._tts_provider.get_status()
        return {"model_loaded": False, "device": "none", "status": "unavailable"}

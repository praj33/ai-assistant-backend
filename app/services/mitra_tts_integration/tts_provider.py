"""
tts_provider.py — Text-to-Speech Provider for Mitra AI

Embeds the Vaani XTTS engine directly into Mitra (no external API needed).
Includes all production guardrails from Gurukul:
  - 5000 character input limit
  - 20 second inference timeout
  - Max 3 concurrent requests
  - Retry with backoff
  - In-memory caching
  - GPU→CPU automatic fallback
"""

import asyncio
import hashlib
import time
import os
import uuid
import logging
from typing import Optional

logger = logging.getLogger("TTSProvider")

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
MAX_INPUT_CHARS   = 5000
INFERENCE_TIMEOUT = 20      # seconds
MAX_CONCURRENCY   = 3
MAX_RETRIES       = 3
CACHE_MAX         = 200

# Directories (relative to this file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_SAMPLES_DIR = os.path.join(BASE_DIR, "voice_samples")
AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, "audio_output")


class TTSProvider:
    """
    Embedded TTS engine using Coqui XTTS v2.
    Loads the model directly — no external API call needed.
    """

    def __init__(self):
        self.model = None
        self.device = "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        self.cache = {}
        self.start_time = time.time()
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failures": 0,
            "timeouts": 0,
            "cache_hits": 0,
        }
        self._model_loaded = False

    def load_model(self):
        """
        Load the XTTS model. Call this once at startup.
        Automatically detects GPU and falls back to CPU.
        """
        if self._model_loaded:
            return

        try:
            import torch
            from TTS.api import TTS

            os.environ["COQUI_TOS_AGREED"] = "1"

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"[TTS] Loading model {self.model_name} on {self.device}...")

            self.model = TTS(self.model_name).to(self.device)
            self._model_loaded = True
            logger.info(f"[TTS] Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"[TTS] Model load failed: {e}")
            # Try CPU fallback
            try:
                import torch
                from TTS.api import TTS

                self.device = "cpu"
                logger.info("[TTS] Retrying on CPU...")
                self.model = TTS(self.model_name).to("cpu")
                self._model_loaded = True
                logger.info("[TTS] Model loaded on CPU (fallback)")
            except Exception as e2:
                logger.error(f"[TTS] CPU fallback also failed: {e2}")
                raise RuntimeError(f"TTS model failed to load: {e2}")

    async def generate_audio(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Generate speech audio from text.

        Args:
            text: Text to synthesize (max 5000 chars).
            language: ISO 639-1 language code.

        Returns:
            bytes: WAV audio data.

        Raises:
            ValueError: If text is empty or too long.
            TimeoutError: If inference exceeds 20 seconds.
        """
        # 1. Validation
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        if len(text) > MAX_INPUT_CHARS:
            raise ValueError(
                f"Input length {len(text)} exceeds maximum {MAX_INPUT_CHARS} characters"
            )

        # 2. Ensure model is loaded
        if not self._model_loaded:
            await asyncio.to_thread(self.load_model)

        # 3. Cache check
        cache_key = hashlib.sha256(f"{language}:{text}".encode()).hexdigest()
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]

        # 4. Concurrency control + timeout
        self.stats["total_requests"] += 1

        async with self.semaphore:
            try:
                audio_data = await asyncio.wait_for(
                    self._generate(text, language),
                    timeout=INFERENCE_TIMEOUT,
                )
                # Cache result
                if len(self.cache) >= CACHE_MAX:
                    oldest = next(iter(self.cache))
                    del self.cache[oldest]
                self.cache[cache_key] = audio_data
                self.stats["successful"] += 1
                return audio_data

            except asyncio.TimeoutError:
                self.stats["timeouts"] += 1
                self.stats["failures"] += 1
                raise TimeoutError(f"TTS inference timed out after {INFERENCE_TIMEOUT}s")

    async def _generate(self, text: str, language: str) -> bytes:
        """Run XTTS inference in a thread (blocking operation)."""
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                audio_data = await asyncio.to_thread(
                    self._sync_generate, text, language
                )
                if audio_data:
                    return audio_data
                raise RuntimeError("Empty audio generated")
            except Exception as e:
                last_error = e
                logger.warning(f"[TTS] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1 * attempt)

        self.stats["failures"] += 1
        raise RuntimeError(f"TTS failed after {MAX_RETRIES} attempts: {last_error}")

    def _sync_generate(self, text: str, language: str) -> bytes:
        """Synchronous XTTS inference."""
        # Find reference voice
        ref_path = os.path.join(VOICE_SAMPLES_DIR, "reference.wav")
        if not os.path.exists(ref_path):
            # Fallback to any WAV file
            if os.path.exists(VOICE_SAMPLES_DIR):
                wavs = [f for f in os.listdir(VOICE_SAMPLES_DIR) if f.endswith(".wav")]
                if wavs:
                    ref_path = os.path.join(VOICE_SAMPLES_DIR, wavs[0])
                else:
                    raise FileNotFoundError(
                        f"No reference voice samples found in {VOICE_SAMPLES_DIR}"
                    )
            else:
                raise FileNotFoundError(f"Voice samples directory not found: {VOICE_SAMPLES_DIR}")

        # Generate to temp file
        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(AUDIO_OUTPUT_DIR, f"voice_{uuid.uuid4()}.wav")

        self.model.tts_to_file(
            text=text,
            speaker_wav=ref_path,
            language=language.lower()[:2],  # XTTS uses 2-char codes
            file_path=output_path,
        )

        # Read and return bytes
        with open(output_path, "rb") as f:
            audio_data = f.read()

        # Cleanup temp file
        try:
            os.remove(output_path)
        except OSError:
            pass

        return audio_data

    def get_status(self) -> dict:
        """Return operational metrics."""
        return {
            "model_loaded": self._model_loaded,
            "device": self.device,
            "uptime_seconds": int(time.time() - self.start_time),
            "total_requests": self.stats["total_requests"],
            "successful": self.stats["successful"],
            "failures": self.stats["failures"],
            "timeouts": self.stats["timeouts"],
            "cache_hits": self.stats["cache_hits"],
            "cache_size": len(self.cache),
        }


# ──────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────
tts_provider = TTSProvider()

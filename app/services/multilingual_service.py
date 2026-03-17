"""
MultilingualService — Language Detection & Translation for Mitra AI

Uses mitra_tts_integration's language_detector and translator for
real multilingual capabilities powered by Groq LLM.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("MultilingualService")

# Import from mitra_tts_integration
try:
    from app.services.mitra_tts_integration.language_detector import (
        detect_language as _detect_language_full,
        LANGUAGE_NAMES,
    )
    from app.services.mitra_tts_integration.translator import (
        translate,
        translate_to_english,
        translate_from_english,
    )
    TTS_INTEGRATION_AVAILABLE = True
except ImportError:
    TTS_INTEGRATION_AVAILABLE = False
    LANGUAGE_NAMES = {
        "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
        "de": "German", "ja": "Japanese", "ko": "Korean", "zh-cn": "Chinese",
        "ar": "Arabic",
    }
    logger.warning("[MultilingualService] mitra_tts_integration not available, translation disabled")


class MultilingualService:
    def __init__(self):
        pass

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        Returns ISO 639-1 language code (e.g., "hi", "en").
        """
        normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
        if self._is_short_english_utterance(normalized):
            return "en"

        if TTS_INTEGRATION_AVAILABLE:
            try:
                result = _detect_language_full(text)
                return result.get("code", "en")
            except Exception as e:
                logger.warning(f"[MultilingualService] Detection failed: {e}")
                return "en"
        else:
            # Basic fallback using langdetect directly
            try:
                import langdetect
                detected = langdetect.detect(text)
                return detected
            except Exception:
                return "en"

    @staticmethod
    def _is_short_english_utterance(text: str) -> bool:
        if not text:
            return True
        if not text.isascii():
            return False

        short_phrases = {
            "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
            "who are you", "what is your name", "what's your name",
            "what can you do", "how are you",
        }
        if text in short_phrases:
            return True

        words = [part for part in text.split(" ") if part]
        greeting_tokens = {"hi", "hello", "hey"}
        if words and words[0] in greeting_tokens and len(words) <= 4:
            return True

        if len(words) <= 3 and all(word in {"hi", "hello", "hey", "thanks", "bye"} for word in words):
            return True

        return False

    def translate_text(self, text: str, target_lang: str, source_lang: str = None) -> str:
        """
        Translate text from source language to target language using Groq LLM.
        """
        if not text or not text.strip():
            return text

        if target_lang == source_lang:
            return text

        if not TTS_INTEGRATION_AVAILABLE:
            logger.warning("[MultilingualService] Translation not available, returning original text")
            return text

        try:
            return translate(text, target_language=target_lang, source_language=source_lang or "auto")
        except Exception as e:
            logger.error(f"[MultilingualService] Translation failed: {e}")
            return text

    def translate_to_english(self, text: str, source_lang: str = "auto") -> str:
        """Translate any language → English."""
        if not TTS_INTEGRATION_AVAILABLE:
            return text
        try:
            return translate_to_english(text, source_language=source_lang)
        except Exception as e:
            logger.error(f"[MultilingualService] Translation to English failed: {e}")
            return text

    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate English → any language."""
        if not TTS_INTEGRATION_AVAILABLE:
            return text
        try:
            return translate_from_english(text, target_language=target_lang)
        except Exception as e:
            logger.error(f"[MultilingualService] Translation from English failed: {e}")
            return text

    def get_language_metadata(self, text: str) -> Dict[str, Any]:
        """
        Get rich language-related metadata for the text.
        """
        if TTS_INTEGRATION_AVAILABLE:
            try:
                result = _detect_language_full(text)
                return {
                    "detected_language": result.get("code", "en"),
                    "language_name": result.get("name", "English"),
                    "confidence": result.get("confidence", 0.5),
                    "needs_translation": result.get("needs_translation", False),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"[MultilingualService] Language metadata failed: {e}")

        # Fallback
        detected = self.detect_language(text)
        return {
            "detected_language": detected,
            "language_name": LANGUAGE_NAMES.get(detected, detected.upper()),
            "confidence": 0.9,
            "needs_translation": detected != "en",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def validate_language_support(self, language_code: str) -> bool:
        """Check if the given language is supported by the system."""
        return language_code in LANGUAGE_NAMES

    def get_supported_languages(self) -> list:
        """Get list of supported language codes."""
        return list(LANGUAGE_NAMES.keys())

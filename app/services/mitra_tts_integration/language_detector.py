"""
language_detector.py — Automatic Language Detection for Mitra AI

Detects the language of incoming user input using the `langdetect` library.
This must run BEFORE mediation validation in Mitra's pipeline.

Supported languages: English, Hindi, Marathi, Gujarati, Tamil, Spanish, French, etc.
"""

import logging
from typing import Optional

logger = logging.getLogger("LanguageDetector")

# Language code to name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "pa": "Punjabi",
    "ml": "Malayalam",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-cn": "Chinese (Simplified)",
    "pt": "Portuguese",
    "ru": "Russian",
    "it": "Italian",
}

# Internal processing language
INTERNAL_LANGUAGE = "en"


def detect_language(text: str) -> dict:
    """
    Detect the language of the input text.

    Args:
        text: User input text in any language.

    Returns:
        dict with:
            - code: ISO 639-1 language code (e.g., "hi")
            - name: Human-readable name (e.g., "Hindi")
            - confidence: Detection confidence (0.0 to 1.0)
            - needs_translation: Whether text needs translation to English
    """
    if not text or not text.strip():
        return {
            "code": INTERNAL_LANGUAGE,
            "name": "English",
            "confidence": 1.0,
            "needs_translation": False,
        }

    try:
        from langdetect import detect_langs

        results = detect_langs(text)

        if results:
            top = results[0]
            lang_code = str(top.lang)
            confidence = round(top.prob, 3)

            lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
            needs_translation = lang_code != INTERNAL_LANGUAGE

            logger.info(
                f"[LangDetect] Detected: {lang_name} ({lang_code}) "
                f"confidence={confidence} | needs_translation={needs_translation}"
            )

            return {
                "code": lang_code,
                "name": lang_name,
                "confidence": confidence,
                "needs_translation": needs_translation,
            }

    except Exception as e:
        logger.warning(f"[LangDetect] Detection failed: {e}. Defaulting to English.")

    # Default to English on failure
    return {
        "code": INTERNAL_LANGUAGE,
        "name": "English",
        "confidence": 0.5,
        "needs_translation": False,
    }


def is_supported_language(lang_code: str) -> bool:
    """Check if a language is supported."""
    return lang_code in LANGUAGE_NAMES

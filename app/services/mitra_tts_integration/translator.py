"""
translator.py — Text Translation for Mitra AI

Translates text between languages using Groq API (LLM-based translation).
Used in two places in the pipeline:
  1. Input: User's language → English (for Mitra processing)
  2. Output: English → User's language (for response delivery)

Uses the same Groq approach as Gurukul's tts_core_functions.py.
"""

import os
import re
import logging
import requests
from typing import Optional

logger = logging.getLogger("Translator")

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_ENDPOINT = os.getenv(
    "GROQ_API_ENDPOINT",
    "https://api.groq.com/openai/v1/chat/completions"
)
FAST_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "gu": "Gujarati",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "bn": "Bengali",
    "pa": "Punjabi", "ml": "Malayalam", "es": "Spanish", "fr": "French",
    "de": "German", "ar": "Arabic", "ja": "Japanese", "ko": "Korean",
    "zh-cn": "Chinese (Simplified)", "pt": "Portuguese", "ru": "Russian",
    "it": "Italian",
}


def _remove_emojis(text: str) -> str:
    """Remove emojis from text to prevent translation issues."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def translate(text: str, target_language: str, source_language: str = "auto") -> str:
    """
    Translate text to the target language using Groq API.

    Args:
        text: Text to translate.
        target_language: Target language code (e.g., "hi", "en").
        source_language: Source language code (default: "auto").

    Returns:
        Translated text. Returns original text if translation fails.
    """
    if not text or not text.strip():
        return text

    target_lang_name = LANGUAGE_NAMES.get(target_language, target_language)

    # No translation needed if target is same as source
    if target_language == source_language:
        return text

    # No translation needed if target is English and input looks English
    if target_language == "en" and source_language == "en":
        return text

    # Clean emojis
    text = _remove_emojis(text)

    api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("[Translator] No GROQ_API_KEY found, returning original text")
        return text

    # Build translation prompt
    system_prompt = f"""You are a translation tool. Your ONLY job is to translate the given text to {target_lang_name}.

RULES:
- Translate ONLY the provided text
- Do NOT add any explanations, notes, or additional information
- Do NOT add context or examples
- Return ONLY the translation, nothing else
- If the text is already in {target_lang_name}, return it unchanged"""

    user_prompt = f"Translate this text to {target_lang_name}:\n\n{text}"

    word_count = len(text.split())
    max_tokens = min(max(word_count * 2, 100), 500)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": FAST_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }

    # Try fast model, fallback to larger model
    for model in [FAST_MODEL, FALLBACK_MODEL]:
        try:
            payload["model"] = model
            response = requests.post(
                GROQ_API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=15,
            )

            if response.status_code == 200:
                result = response.json()
                translated = result["choices"][0]["message"]["content"].strip()
                translated = _clean_translation(translated, target_lang_name)

                logger.info(
                    f"[Translator] {source_language}→{target_language} | "
                    f"model={model} | {len(text)}→{len(translated)} chars"
                )
                return translated

        except Exception as e:
            logger.warning(f"[Translator] Model {model} failed: {e}")
            continue

    logger.error("[Translator] All models failed, returning original text")
    return text


def _clean_translation(text: str, target_lang_name: str) -> str:
    """Remove common LLM artifacts from translation output."""
    # Strip quotes
    text = text.strip('"').strip("'").strip()

    # Remove common prefixes
    for prefix in [
        f"{target_lang_name}:", "Translation:", "Translated text:",
        "Here is the translation:", "The translation is:",
    ]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    # Remove notes/explanations
    for sep in ["\n\nNote:", "\n\nAlso:", "\n\nAdditionally:", "\n\n---"]:
        if sep in text:
            text = text.split(sep)[0].strip()

    return text


def translate_to_english(text: str, source_language: str = "auto") -> str:
    """Shortcut: translate any language → English."""
    return translate(text, target_language="en", source_language=source_language)


def translate_from_english(text: str, target_language: str) -> str:
    """Shortcut: translate English → any language."""
    return translate(text, target_language=target_language, source_language="en")

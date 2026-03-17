"""
mitra_voice_pipeline.py — Main Integration Point for Mitra AI

This is the file you wire into Mitra's response pipeline.
It handles the full flow:
  1. Detect input language
  2. Translate to English for Mitra processing
  3. Call Mitra's existing logic (passed as a function)
  4. Translate response back to user's language
  5. Generate voice audio (optional)

Usage:
    from mitra_tts_integration.mitra_voice_pipeline import process_multilingual_request

    result = await process_multilingual_request(
        user_input="नमस्ते, मुझे गणित सिखाओ",
        mitra_process_fn=your_mitra_function,
        generate_voice=True
    )
"""

import logging
from typing import Callable, Optional, Any

from .language_detector import detect_language
from .translator import translate_to_english, translate_from_english
from .tts_provider import tts_provider

logger = logging.getLogger("MitraVoicePipeline")


async def process_multilingual_request(
    user_input: str,
    mitra_process_fn: Callable,
    generate_voice: bool = False,
    force_language: Optional[str] = None,
) -> dict:
    """
    Complete multilingual + voice pipeline for Mitra.

    Args:
        user_input:        The raw user message (any language).
        mitra_process_fn:  Your existing Mitra processing function.
                           Should accept (text: str) and return a response string.
                           Can be sync or async.
        generate_voice:    If True, also generate audio of the response.
        force_language:    Override language detection with this code (e.g., "hi").

    Returns:
        dict with:
            - detected_language: str (ISO 639-1 code)
            - language_name: str (human readable)
            - original_input: str
            - translated_input: str (English version)
            - mitra_response_english: str (Mitra's response in English)
            - response_in_user_language: str (translated back)
            - audio_bytes: bytes or None (WAV audio if generate_voice=True)
            - pipeline_status: str ("success" or "partial" or "error")
    """
    result = {
        "detected_language": "en",
        "language_name": "English",
        "original_input": user_input,
        "translated_input": user_input,
        "mitra_response_english": "",
        "response_in_user_language": "",
        "audio_bytes": None,
        "pipeline_status": "success",
    }

    try:
        # ── Step 1: Language Detection ────────────────────────
        if force_language:
            lang_info = {"code": force_language, "name": force_language, "needs_translation": force_language != "en"}
        else:
            lang_info = detect_language(user_input)

        result["detected_language"] = lang_info["code"]
        result["language_name"] = lang_info.get("name", lang_info["code"])

        logger.info(f"[Pipeline] Language: {lang_info['code']} | Input: {user_input[:50]}...")

        # ── Step 2: Translate to English ──────────────────────
        if lang_info.get("needs_translation", False):
            english_input = translate_to_english(user_input, source_language=lang_info["code"])
            result["translated_input"] = english_input
            logger.info(f"[Pipeline] Translated to English: {english_input[:50]}...")
        else:
            english_input = user_input
            result["translated_input"] = user_input

        # ── Step 3: Mitra Processes (in English) ──────────────
        import asyncio
        if asyncio.iscoroutinefunction(mitra_process_fn):
            mitra_response = await mitra_process_fn(english_input)
        else:
            mitra_response = mitra_process_fn(english_input)

        result["mitra_response_english"] = str(mitra_response)

        # ── Step 4: Translate Response Back ───────────────────
        if lang_info.get("needs_translation", False):
            user_lang_response = translate_from_english(
                str(mitra_response), target_language=lang_info["code"]
            )
            result["response_in_user_language"] = user_lang_response
            logger.info(f"[Pipeline] Translated response to {lang_info['code']}")
        else:
            result["response_in_user_language"] = str(mitra_response)

        # ── Step 5: Generate Voice (optional) ─────────────────
        if generate_voice:
            try:
                # Use the response in user's language for TTS
                tts_text = result["response_in_user_language"]
                tts_lang = lang_info["code"]

                audio_bytes = await tts_provider.generate_audio(tts_text, language=tts_lang)
                result["audio_bytes"] = audio_bytes
                logger.info(f"[Pipeline] Audio generated: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.warning(f"[Pipeline] TTS failed (non-fatal): {e}")
                result["audio_bytes"] = None
                result["pipeline_status"] = "partial"  # Text OK, audio failed

    except Exception as e:
        logger.error(f"[Pipeline] Error: {e}")
        result["pipeline_status"] = "error"
        result["mitra_response_english"] = f"Pipeline error: {str(e)}"
        result["response_in_user_language"] = result["mitra_response_english"]

    return result

# Multilingual Normalization Flow

## Overview
The goal of language normalization is to ensure that the core components of Mitra (Mediation, Safety, Intelligence, Enforcement, and Orchestration) can operate agnostically to the user's spoken language. They expect, process, and analyze English text exclusively.

## Normalization Steps

1. **Detect Language**: The input is scanned by `MultilingualService.get_language_metadata()`. If `needs_translation` is True, it enters the normalization flow.
2. **Translate to Internal Language (English)**:
   - `MultilingualService.translate_to_english()` is invoked.
   - This service currently delegates to the `translator.py` module, which interfaces with a fast Groq LLM (e.g., Llama 3.1 8B Instant) under strict translation prompts.
   - The original text is temporarily stored, but the primary request payload is overwritten with the English translation.
3. **Core Processing**: The English text passes through the Mediation Validation (Safety Gate), Intelligence (Intent Analysis), Enforcement, and Orchestration flows.
4. **Translate Response Back**:
   - Once the downstream components finalize their Response Text (in English).
   - The Orchestrator calls `MultilingualService.translate_from_english(response_text, target_language)` which translates the English content back into the user's detected language.

By executing this cycle, Mitra natively understands and replies in over 20 languages without requiring every downstream microservice to be localized.

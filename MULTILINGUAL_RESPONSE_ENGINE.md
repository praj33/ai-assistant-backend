# Multilingual Response Engine

## Overview
The Multilingual Response Engine enables Mitra to serve diverse language speakers natively by generating responses in the user's original language, rather than English. 

## Translation Mechanism
Mitra avoids expensive or rate-limited direct APIs (like Google Translate) by leveraging high-speed LLMs (via Groq inference). 

1. **Agnostic Generation**: All intelligence workflows and general fallback mechanisms natively generate responses in English. This consolidates testing and enforces consistent persona guidelines.
2. **Inverse Translation Trigger**: 
   - Before the API response JSON is packaged, the orchestrator checks `target_language`.
   - If `target_language != "en"`, the `MultilingualService` is invoked.
3. **Groq LLM Execution**:
   - System Prompt: `You are a translation tool. Your ONLY job is to translate the given text to {target_lang_name}. RULES: Translate ONLY the provided text...`
   - Model Selection: Defaults to `llama-3.1-8b-instant` for ultra-low latency, falling back to `llama-3.3-70b-versatile`.
   - Artifact Cleanup: Emojis are temporarily stripped and reattached if necessary, and common LLM artifacts (like "Here is the translation:") are programmatically stripped via `_clean_translation()`.
4. **Delivery**: The translated response string replaces the English string in the final API envelope.

This approach guarantees high-fidelity, context-aware translations (since LLMs capture nuance better than traditional statistical translation engines) at extremely high speeds.

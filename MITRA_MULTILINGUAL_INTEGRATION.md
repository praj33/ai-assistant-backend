# Mitra Multilingual Integration

## System Configuration 
Mitra's AI-Assistant-Backend has been heavily refactored to seamlessly support language detection, LLM-based translation, and local, offline Text-to-Speech synthesis.

### Integration Points
1. `app/services/multilingual_service.py`: Replaced local dictionary-based mocks with the dynamic `langdetect` and `Groq` API backend modules imported from `mitra_tts_integration`.
2. `app/services/audio_service.py`: Stripped out reliance on `gTTS` and Google's HTTP-based speech system to integrate a custom `TTSProvider` instance.
3. `app/core/assistant_orchestrator.py`: Wired the language pipeline directly underneath the payload ingestion boundary, normalizing every input globally across the app *before* it passes the initial safety gates, enforcing strict isolation.

### Configuration API
The Orchestrator's `AssistantContext` schema allows explicit overrides or feature toggles natively:
- `preferred_language`: Defaults to `"auto"`. Explicitly setting this overrides the `langdetect` engine and forces output synthesis to that ISO 639-1 localized model.
- `audio_output_requested`: Toggling this boolean within the frontend payload informs the `AudioService` downstream whether to incur the expensive inference cycle to package binary voice data inside the response envelope.

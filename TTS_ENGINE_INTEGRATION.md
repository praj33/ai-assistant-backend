# TTS Engine Integration

## Overview
Mitra's audio pipeline required a resilient, open-source text-to-speech engine to avoid the costs and restrictions of external paid APIs. We have integrated the **Coqui XTTS v2** model as the primary TTS engine.

## Choosing Coqui XTTS
- **Open-Source Priority**: Adhering to the mandate to use sovereign or open-source speech systems, Coqui XTTS is hosted directly within Mitra's environment.
- **Multilingual Native**: XTTS v2 natively supports high-quality synthesis in multiple languages (English, French, Spanish, German, Italian, Portuguese, Arabic, Hindi, Japanese, Korean, Chinese, etc.).
- **Voice Cloning**: It supports zero-shot voice cloning given a short reference `.wav`, establishing a consistent "Mitra" voice identity across all languages.

## Infrastructure Integration
The `TTSProvider` singleton (`tts_provider.py`) handles the engine lifecycle:
1. **Lazy Loading**: The model (which is several gigabytes in size) is not loaded into memory until the first active speech request, maintaining fast initial API startup times.
2. **Device Detection**: PyTorch automatically detects CUDA availability. If a GPU is present, it uses `cuda`; if not, or if inference fails, it gracefully falls back to `cpu` execution.
3. **Guardrails**:
   - `MAX_CONCURRENCY = 3`: Prevents Out-Of-Memory (OOM) errors by queuing requests via asyncio semaphores.
   - `INFERENCE_TIMEOUT = 20s`: Aborts hanging generation attempts to prevent blocking the async event loop.
   - `In-Memory Caching`: Caches identical generated responses (up to 200 items) based on a text + language SHA256 hash to save computational cycles on repeated greetings.

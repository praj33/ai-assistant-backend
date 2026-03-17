# Mitra AI — TTS + Multilingual Integration Package

This folder contains everything needed to add **multilingual input + voice output** to Mitra AI.

---

## What's Inside

| File | Purpose |
|------|---------|
| `language_detector.py` | Detects input language using `langdetect` |
| `translator.py` | Translates text between languages using Groq API |
| `tts_provider.py` | Text-to-Speech via Vaani XTTS engine (with guardrails) |
| `mitra_voice_pipeline.py` | **Main integration point** — plug this into Mitra's response flow |
| `requirements.txt` | Python dependencies to install |

---

## How to Integrate into Mitra

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set environment variable
```bash
# Groq API key (for translation)
export GROQ_API_KEY="your-groq-api-key"
```

### Step 3: Copy this folder into Mitra's backend
```
mitra/
  services/
    mitra_tts_integration/    ← put this folder here
      language_detector.py
      translator.py
      tts_provider.py
      mitra_voice_pipeline.py
```

### Step 4: Wire into Mitra's response pipeline
Wherever Mitra generates a response, wrap it like this:

```python
from services.mitra_tts_integration.mitra_voice_pipeline import process_multilingual_request

result = await process_multilingual_request(
    user_input="नमस्ते, मुझे गणित सिखाओ",
    mitra_process_fn=your_existing_mitra_function,  # Your existing Mitra logic
    generate_voice=True  # Set False for text-only
)

# result = {
#     "detected_language": "hi",
#     "original_input": "नमस्ते, मुझे गणित सिखाओ",
#     "translated_input": "Hello, teach me math",
#     "mitra_response_english": "Sure! Let's start with...",
#     "response_in_user_language": "ज़रूर! चलिए शुरू करते हैं...",
#     "audio_bytes": b"...",  # WAV audio (or None if generate_voice=False)
# }
```

### Pipeline Flow
```
User Input (any language)
  → language_detector.py  (detect: "hi")
  → translator.py         (Hindi → English)
  → Mitra processes normally (in English)
  → translator.py         (English → Hindi)
  → tts_provider.py       (Hindi text → Hindi audio)
  → Return { text + audio }
```

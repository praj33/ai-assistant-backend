# Language Detection Layer

## Overview
The Language Detection Layer is the very first step in Mitra's processing pipeline, executing immediately after a user's input is received and before any mediation, safety, or orchestration logic runs.

## How Detection Works
Mitra uses the `langdetect` library (an open-source language detection port of Google's language-detection library) to analyze the incoming text.

1. **Short English Utterance Fast-Path**: To improve performance and prevent false positives on short greetings (e.g., "hi", "hello", "bye"), a fast-path regex and token check immediately classifies known English short-phrases as `en`.
2. **Probabilistic Detection**: For all other inputs, `langdetect` calculates the probabilities of the text belonging to various supported languages (Hindi, Marathi, Gujarati, Tamil, Spanish, French, etc.).
3. **Metadata Generation**: The detector returns a rich metadata object containing:
   - `detected_language`: The ISO 639-1 code (e.g., `hi`)
   - `language_name`: Human-readable name (e.g., `Hindi`)
   - `confidence`: The probability score
   - `needs_translation`: A boolean flag determining if the input is non-English and requires normalization.

## Pipeline Placement
The detection occurs at line ~480 of `app/core/assistant_orchestrator.py`:
```
Input text -> [Language Detection] -> [Normalization to English] -> [Safety Gate] -> ...
```
By placing this before the `call_safety_service` (Mediation/Safety gate), we ensure that the rest of the pipeline can operate natively in English without needing multilingual support in downstream components.

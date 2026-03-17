# Voice Output Pipeline

## Overview
The Voice Output Pipeline is the final stage of the request lifecycle when the user includes `audio_output_requested: True` in the assistant payload context.

## Pipeline Flow

1. **Response Text Complete**: The orchestrator has finalized the translated string in the user's detected language.
2. **Audio Request Gate**: 
   - `if request.context.audio_output_requested:`
   - The Orchestrator calls the `AudioService` (specifically the async definition `await audio_service.text_to_speech_async()`).
3. **Engine Activation**:
   - `AudioService` routes the request directly to the `TTSProvider` instance running the Coqui XTTS v2 model.
   - The provider limits the text length (up to 5000 chars) to prevent inference OOM, hashes the content to check its LRU cache, and if it's a cache miss, enters the semaphore lock.
4. **Audio Synthesis**:
   - The Coqui XTTS model synthesizes the waveform asynchronously.
   - Using a fallback-resistant `tts_to_file` approach within an ephemeral `.wav` file space, the model dumps the output and loads the binary representation back into memory.
5. **Delivery**:
   - The orchestrator packages the bytes into the final JSON response's `audio_response` attribute, ensuring that the frontend receives the message text simultaneously with the high-fidelity binary audio.
   
Alternatively, developers can use the decoupled dedicated HTTP route `POST /api/tts` to access this backend text-to-speech functionality directly.

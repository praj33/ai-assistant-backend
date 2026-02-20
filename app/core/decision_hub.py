from typing import Dict, Any, Optional, Union
import json
import os
import httpx
import base64
from io import BytesIO

class DecisionHub:
    def __init__(self):
        # Ensure data directory exists
        memory_dir = "data"
        self.memory_file = os.path.join(memory_dir, "memory.json")
        try:
            os.makedirs(memory_dir, exist_ok=True)
            if not os.path.exists(self.memory_file):
                with open(self.memory_file, 'w') as f:
                    json.dump({}, f)
        except Exception as e:
            # If file operations fail (e.g., read-only filesystem), use in-memory
            print(f"Warning: Could not create memory file: {e}. Using in-memory storage.")
            self.memory_file = None
            self._memory_cache = {}

    def load_memory(self) -> Dict[str, Any]:
        if self.memory_file is None:
            return self._memory_cache
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Could not load memory file: {e}. Using in-memory storage.")
            return self._memory_cache if hasattr(self, '_memory_cache') else {}

    def save_memory(self, memory: Dict[str, Any]):
        if self.memory_file is None:
            self._memory_cache = memory
            return
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f)
        except Exception as e:
            print(f"Warning: Could not save memory file: {e}. Using in-memory storage.")
            if not hasattr(self, '_memory_cache'):
                self._memory_cache = {}
            self._memory_cache = memory

    async def process_voice_input(self, audio_data: bytes, content_type: str = "audio/wav") -> Dict[str, Any]:
        """Process voice input using STT API"""
        try:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            async with httpx.AsyncClient() as client:
                files = {"file": ("audio.wav", BytesIO(audio_data), content_type)}
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                response = await client.post(f"{base_url}/api/voice_stt", files=files, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"STT API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to process voice input: {str(e)}")

    async def generate_voice_output(self, text: str, voice: str = "alloy", model: str = "tts-1") -> Dict[str, Any]:
        """Generate voice output using TTS API"""
        try:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            async with httpx.AsyncClient() as client:
                payload = {"text": text, "voice": voice, "model": model}
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                response = await client.post(f"{base_url}/api/voice_tts", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"TTS API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to generate voice output: {str(e)}")

    async def create_task(self, description: str) -> Dict[str, Any]:
        """Create a new task using Task API"""
        try:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            async with httpx.AsyncClient() as client:
                payload = {"description": description}
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                response = await client.post(f"{base_url}/api/tasks", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Task API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to create task: {str(e)}")

    async def generate_response(self, query: str, intent: str, context: Dict[str, Any] = None, model: str = "uniguru") -> Dict[str, Any]:
        """Generate response using Respond or Summarize API based on intent"""
        try:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            async with httpx.AsyncClient() as client:
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                if intent == "summarize":
                    payload = {"text": query, "model": model}
                    response = await client.post(f"{base_url}/api/summarize", json=payload, headers=headers)
                else:
                    payload = {"query": query, "context": context or {}, "model": model}
                    response = await client.post(f"{base_url}/api/respond", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Response API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")

    async def make_decision(self, input_text: str, platform: str = "web", device_context: str = "desktop", voice_input: bool = False, audio_data: Optional[bytes] = None) -> Dict[str, Any]:
        # Platform-aware scoring including VR
        platform_scores = {
            "mobile": {"voice": 0.9, "text": 0.7},
            "web": {"voice": 0.5, "text": 0.8},
            "desktop": {"voice": 0.6, "text": 0.9},
            "vr": {"voice": 0.95, "text": 0.6}  # VR prefers voice
        }

        processed_text = input_text
        stt_result = None
        action_type = "text"

        # Process voice input if provided
        if voice_input and audio_data:
            try:
                stt_result = await self.process_voice_input(audio_data)
                processed_text = stt_result.get("text", input_text)
                action_type = "voice"
            except Exception as e:
                print(f"Voice processing failed: {e}. Using original text.")
                processed_text = input_text
        elif voice_input or "voice" in input_text.lower() or "speak" in input_text.lower():
            action_type = "voice"

        # Detect intent from processed text
        try:
            intent_data = await self.detect_intent(processed_text)
            intent = intent_data["intent"]
        except Exception as e:
            print(f"Intent detection failed: {e}. Using fallback.")
            intent_data = {
                "intent": "general",
                "entities": {},
                "context": {"priority": "normal"},
                "original_text": processed_text,
                "confidence": 0.5
            }
            intent = intent_data["intent"]

        # Get task classification
        try:
            task_data = await self.call_task_api(intent_data)
        except Exception as e:
            print(f"Task classification failed: {e}")
            task_data = {"task": {"task_type": "general_task", "parameters": {}, "priority": "normal"}}

        # BHIV routing
        if intent in ["complex", "multi-step", "research", "analysis"]:
            return {"final_decision": "bhiv_core", "intent": intent, "processed_text": processed_text, "task_data": task_data}

        score = platform_scores.get(device_context, {"voice": 0.5, "text": 0.5})[action_type]

        # Select agent and LLM based on platform and intent
        if device_context == "vr":
            selected_agent = "vr_agent"
            preferred_llm = "mistral"
        elif score > 0.8:
            selected_agent = "voice_agent"
            preferred_llm = "groq"
        elif score > 0.7:
            selected_agent = "text_agent"
            preferred_llm = "chatgpt"
        else:
            selected_agent = "default"
            preferred_llm = "uniguru"

        # Memory reference from long-term JSON DB
        memory = self.load_memory()
        memory_ref = memory.get(processed_text[:50], None)

        # Initialize decision with basic info
        decision = {
            "final_decision": "respond" if action_type == "text" else "voice_response",
            "confidence": score,
            "selected_agent": selected_agent,
            "preferred_llm": preferred_llm,
            "device_context": device_context,
            "memory_reference": memory_ref,
            "intent": intent,
            "processed_text": processed_text
        }

        # Execute real integrations based on intent
        try:
            if intent == "task":
                # Create a task
                task_result = await self.create_task(processed_text)
                decision["task_created"] = task_result
                decision["final_decision"] = "task_created"
            elif intent == "summarize":
                # Generate summary
                response_result = await self.generate_response(processed_text, intent, {"platform": platform, "device": device_context}, preferred_llm)
                decision["response"] = response_result.get("summary")
                decision["final_decision"] = "summary_generated"
            else:
                # Generate general response
                response_result = await self.generate_response(processed_text, intent, {"platform": platform, "device": device_context}, preferred_llm)
                decision["response"] = response_result.get("response")
                decision["final_decision"] = "response_generated"

            # Generate voice output if voice action
            if action_type == "voice" and "response" in decision:
                try:
                    voice_result = await self.generate_voice_output(decision["response"])
                    decision["voice_output"] = voice_result
                except Exception as e:
                    print(f"Voice generation failed: {e}")
                    decision["voice_error"] = str(e)

        except Exception as e:
            print(f"Integration execution failed: {e}")
            decision["integration_error"] = str(e)
            # Fallback to basic response
            decision["final_decision"] = "fallback_response"

        # Update long-term memory
        memory[processed_text[:50]] = decision
        self.save_memory(memory)

        return decision

    async def call_task_api(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the task classification API."""
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                response = await client.post(f"{base_url}/api/task", json=intent_data, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Task API call failed: {e}")
                raise

    async def detect_intent(self, text: str) -> Dict[str, Any]:
        # Use real LLM-based intent detection via internal API
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-Key": os.getenv("API_KEY", "")}
                response = await client.post(f"{base_url}/api/intent", json={"text": text}, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data  # Return full response
            except Exception as e:
                # Fallback to keyword matching if API is unavailable
                print(f"Intent detection API failed: {e}. Using fallback.")
                intent = "general"
                if "summarize" in text.lower():
                    intent = "summarize"
                elif "task" in text.lower():
                    intent = "task"
                # Return fallback dict
                return {
                    "intent": intent,
                    "entities": {},
                    "context": {"priority": "normal"},
                    "original_text": text,
                    "confidence": 0.5
                }

    def simple_response(self, text: str) -> str:
        """Generate a simple synchronous response without async calls"""
        text_lower = text.lower()
        
        # Simple keyword-based responses
        if "hello" in text_lower or "hi" in text_lower:
            return "Hello! How can I assist you today?"
        elif "help" in text_lower:
            return "I'm here to help! You can ask me questions, request tasks, or get information."
        elif "thank" in text_lower:
            return "You're welcome! Is there anything else I can help with?"
        elif "bye" in text_lower or "goodbye" in text_lower:
            return "Goodbye! Have a great day!"
        else:
            return f"I understand: {text}. How can I help you with that?"

decision_hub = DecisionHub()
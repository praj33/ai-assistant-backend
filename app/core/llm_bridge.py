import os
import asyncio
import hashlib
import logging

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from mistralai.client import MistralClient
except ImportError:
    MistralClient = None

logger = logging.getLogger(__name__)


class LLMBridge:
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.groq_client = AsyncGroq(api_key=groq_key) if AsyncGroq and groq_key else None
        self.google_key = os.getenv("GOOGLE_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = MistralClient(api_key=mistral_key) if MistralClient and mistral_key else None

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        self.cache = {}

    async def call_llm(self, model: str, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        prompt = prompt.strip()
        key = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        try:
            # ----- OPENAI -----
            if model == "chatgpt":
                if not self.openai_client:
                    if AsyncOpenAI is None:
                        raise ImportError("openai package is not installed")
                    raise ValueError("OPENAI_API_KEY is not configured")
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GROQ -----
            elif model == "groq":
                if not self.groq_client:
                    if AsyncGroq is None:
                        raise ImportError("groq package is not installed")
                    raise ValueError("GROQ_API_KEY is not configured")
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GEMINI -----
            elif model == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                gemini_model = genai.GenerativeModel("gemini-pro")
                result = await asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={"temperature": 0},
                )
                output = result.text

            # ----- MISTRAL -----
            elif model == "mistral":
                if not self.mistral_client:
                    raise ImportError("mistralai not installed")
                result = await asyncio.to_thread(
                    self.mistral_client.chat,
                    model="mistral-medium",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = result.choices[0].message["content"]

            # ----- UNIGURU -----
            elif model == "uniguru":
                output = f"[UniGuru Mock] Local response to: {prompt[:50]}..."

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            logger.warning("LLM fallback triggered for model %s: %s", model, e)
            # Fallback to mock response on any error
            output = f"[{model.capitalize()} Mock] Response to: Context: {prompt[:50]}..."

        self.cache[key] = output
        return output


llm_bridge = LLMBridge()

import os
import asyncio
import hashlib

from openai import AsyncOpenAI
from groq import AsyncGroq
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from mistralai.client import MistralClient
except ImportError:
    MistralClient = None


class LLMBridge:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.mistral_client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY")) if MistralClient else None

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
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                output = response.choices[0].message.content

            # ----- GROQ -----
            elif model == "groq":
                response = await self.groq_client.chat.completions.create(
                    model="mixtral-8x7b-instruct",
                    messages=[{"role": "user", "content": prompt}]
                )
                output = response.choices[0].message.content

            # ----- GEMINI -----
            elif model == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                gemini_model = genai.GenerativeModel("gemini-pro")
                result = await asyncio.to_thread(gemini_model.generate_content, prompt)
                output = result.text

            # ----- MISTRAL -----
            elif model == "mistral":
                if not self.mistral_client:
                    raise ImportError("mistralai not installed")
                result = await asyncio.to_thread(
                    self.mistral_client.chat,
                    model="mistral-medium",
                    messages=[{"role": "user", "content": prompt}],
                )
                output = result.choices[0].message["content"]

            # ----- UNIGURU -----
            elif model == "uniguru":
                output = f"[UniGuru Mock] Local response to: {prompt[:50]}..."

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            # Fallback to mock response on any error
            output = f"[{model.capitalize()} Mock] Response to: Context: {prompt[:50]}..."

        self.cache[key] = output
        return output


llm_bridge = LLMBridge()

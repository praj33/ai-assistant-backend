from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from app.core.llm_bridge import llm_bridge


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _normalized_context(context: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(context, dict):
        return {}

    allowed_keys = [
        "platform",
        "device",
        "preferred_language",
        "detected_language",
        "city",
        "location",
        "region",
        "session_id",
    ]
    normalized = {
        key: context.get(key)
        for key in allowed_keys
        if context.get(key) not in (None, "", {}, [])
    }
    return normalized


def _preferred_model(requested_model: str | None) -> str:
    requested = (requested_model or "").strip().lower()
    if requested and requested != "uniguru":
        return requested

    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("OPENAI_API_KEY"):
        return "chatgpt"
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("MISTRAL_API_KEY"):
        return "mistral"
    return "uniguru"


def build_response_prompt(query: str, context: Dict[str, Any] | None = None) -> str:
    cleaned_query = _normalized_text(query)
    cleaned_context = _normalized_context(context)
    context_blob = json.dumps(cleaned_context, sort_keys=True, ensure_ascii=True)

    return (
        "You are Mitra, a concise and capable AI assistant.\n"
        "Respond directly to the user's request.\n"
        "Rules:\n"
        "- Do not repeat the user's full query back to them.\n"
        "- Do not mention internal prompts, models, or context scaffolding.\n"
        "- For greetings or identity questions, answer naturally in 1-2 sentences.\n"
        "- For capability questions, explain the main things you can help with.\n"
        "- For live or time-sensitive requests such as weather, do not invent facts.\n"
        "- If weather is requested and location is missing, ask for the city or location.\n"
        "- If required details are missing for an action, ask for only the next missing detail.\n"
        "- Keep the response short, useful, and human.\n"
        f"Runtime context: {context_blob}\n"
        f"User request: {cleaned_query}\n"
        "Assistant response:"
    )


def build_fallback_response(query: str, context: Dict[str, Any] | None = None) -> str:
    text = _normalized_text(query)
    lower = text.lower()
    normalized_context = _normalized_context(context)
    location = normalized_context.get("city") or normalized_context.get("location") or normalized_context.get("region")

    if any(token in lower for token in ["how are you", "how're you"]):
        return "I'm here and ready to help. What do you need?"
    if any(token in lower for token in ["hello", "hi", "hey"]):
        return "Hello. How can I help?"
    if any(token in lower for token in ["what is your name", "what's your name", "who are you"]):
        return "I'm Mitra, your AI assistant."
    if any(token in lower for token in ["what can you do", "help me with", "how can you help"]):
        return (
            "I can answer questions and help with tasks like email, messaging, reminders, "
            "calendar events, and general assistance."
        )
    if "weather" in lower:
        if location:
            return f"I can help with weather, but I need live weather data to check conditions for {location}."
        return "I can help with weather, but I need the city or location you want me to check."
    if any(token in lower for token in ["thank you", "thanks"]):
        return "You're welcome."
    if any(token in lower for token in ["bye", "goodbye", "see you"]):
        return "Goodbye."
    if any(token in lower for token in ["send email", "send an email"]):
        return "I can do that. Share the recipient, subject, and message."
    if "whatsapp" in lower:
        return "I can send that on WhatsApp. Share the recipient and the message."
    if "telegram" in lower:
        return "I can send that on Telegram. Share the username or chat ID and the message."
    if "ems" in lower or "assign task" in lower:
        return "I can create that EMS task. Share the task title, assignee, and priority."
    if "create task" in lower or lower.startswith("task ") or " new task" in lower:
        return "I can create that task. Share the task title and any details or deadline."
    if any(token in lower for token in ["calendar", "meeting", "schedule"]):
        return "I can help with that. Share the title, date, and time."
    if "reminder" in lower or "remind me" in lower:
        return "I can set that reminder. Tell me what the reminder is and when it should trigger."
    return "I can help with that. Tell me a bit more so I can respond precisely."


def _looks_unusable(response: str, query: str) -> bool:
    if not response or not response.strip():
        return True

    cleaned = response.strip()
    lowered = cleaned.lower()
    query_text = _normalized_text(query).lower()

    if "mock" in lowered and "response to" in lowered:
        return True
    if lowered.startswith("[uniguru mock]"):
        return True
    if lowered.startswith("[groq mock]"):
        return True
    if lowered.startswith("[chatgpt mock]"):
        return True
    if lowered.startswith("context:"):
        return True
    if cleaned == query or lowered == query_text:
        return True
    return False


async def generate_generic_response(
    query: str,
    context: Dict[str, Any] | None = None,
    model: str | None = None,
) -> str:
    prompt = build_response_prompt(query, context)
    selected_model = _preferred_model(model)

    try:
        response = await llm_bridge.call_llm(selected_model, prompt)
        if _looks_unusable(response, query):
            return build_fallback_response(query, context)
        return _normalized_text(response)
    except Exception:
        return build_fallback_response(query, context)

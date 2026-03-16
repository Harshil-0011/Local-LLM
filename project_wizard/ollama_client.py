import requests
import json
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"

    def chat(self, model: str, messages: list[dict], **params) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": params
        }

        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            raise RuntimeError(f"Ollama connection error: {e}. Is Ollama running?")

def ollama_chat(base_url: str, model: str, messages: list[dict], **params) -> str:
    client = OllamaClient(base_url)
    return client.chat(model, messages, **params)

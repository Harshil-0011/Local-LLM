import requests
import json
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"

    def chat(self, model: str, messages: list[dict], **params) -> str:
        # Ollama's chat API supports an "images" field within each message object.
        # We ensure the structure is correct as passed from the engine.

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": params
        }

        import time
        start_time = time.time()
        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            duration = time.time() - start_time
            result = response.json()
            content = result.get("message", {}).get("content", "")

            # Simple token estimation: ~4 chars per token
            tokens = len(content) / 4
            self.last_latency = duration
            self.last_tps = tokens / duration if duration > 0 else 0

            return content
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            raise RuntimeError(f"Ollama connection error: {e}. Is Ollama running?")

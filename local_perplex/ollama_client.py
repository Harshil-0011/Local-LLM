import requests
import json
import logging
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"
        self.last_latency = 0.0
        self.last_tps = 0.0

    def chat(self, model: str, messages: list[dict], stream: bool = False, **params):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": params
        }

        if not stream:
            start_time = time.time()
            try:
                response = requests.post(self.chat_url, json=payload, timeout=300)
                response.raise_for_status()
                duration = time.time() - start_time
                result = response.json()
                content = result.get("message", {}).get("content", "")
                tokens = len(content) / 4
                self.last_latency = duration
                self.last_tps = tokens / duration if duration > 0 else 0
                return content
            except Exception as e:
                logger.error(f"Error: {e}")
                raise RuntimeError(f"Ollama error: {e}")
        else:
            return self._stream_chat(payload)

    def _stream_chat(self, payload):
        try:
            response = requests.post(self.chat_url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                    if chunk.get("done"):
                        break
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"\n[Error: {e}]"

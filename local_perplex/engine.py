from .search import SearchEngine
from .ollama_client import OllamaClient
import os
import yaml
from pathlib import Path

class Config:
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.model = "llama3.2:8b"

class LocalPerplex:
    def __init__(self):
        self.config = Config()
        self.search_engine = SearchEngine()
        self.ollama = OllamaClient(self.config.ollama_base_url)

    def ask(self, question: str, mode: str = "industry_standard"):
        num_sources = 20
        sources = self.search_engine.search(question, num_results=num_sources)

        # Select sources based on mode
        if mode == "industry_standard":
            selected_sources = sources[:10]
        else:
            selected_sources = sources

        context = "\n\n".join([f"Source: {s['url']}\nContent: {s['content'][:3000]}" for s in selected_sources])

        system_prompt = (
            "You are a helpful AI assistant. Use the provided sources to answer the user's question accurately. "
            "Always cite your sources using [URL]. If you don't know the answer based on sources, say so."
        )

        if mode == "all_references":
            system_prompt += " Provide a very detailed answer including all possible references from the sources."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]

        answer = self.ollama.chat(self.config.model, messages)
        return answer, selected_sources

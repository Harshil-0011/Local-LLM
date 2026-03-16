from .search import SearchEngine
from .ollama_client import OllamaClient
from .history import HistoryManager
from .documents import DocumentManager
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
        self.history = HistoryManager()
        self.docs = DocumentManager()

    def ask(self, question: str, mode: str = "industry_standard", history: list = None):
        if history is None:
            history = []

        num_sources = 20
        sources = self.search_engine.search(question, num_results=num_sources)

        # Select sources based on mode
        if mode == "industry_standard":
            selected_sources = sources[:10]
        else:
            selected_sources = sources

        context = "\n\n".join([f"Source: {s['url']}\nContent: {s['content'][:3000]}" for s in selected_sources])

        # Add local documents to context
        local_context = self.docs.get_local_context()
        if local_context:
            context = f"--- LOCAL DOCUMENTS ---\n{local_context}\n\n--- WEB SOURCES ---\n{context}"

        system_prompt = (
            "You are a helpful AI assistant. Use the provided sources to answer the user's question accurately. "
            "Always cite your sources using [URL]. If you don't know the answer based on sources, say so."
        )

        if mode == "all_references":
            system_prompt += " Provide a very detailed answer including all possible references from the sources."

        messages = [{"role": "system", "content": system_prompt}]

        # Add history if available
        for h in history:
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})

        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

        answer = self.ollama.chat(self.config.model, messages)

        # Generate related questions
        related_prompt = [
            {"role": "system", "content": "Based on the research answer, suggest 3 concise follow-up questions the user might be interested in. Return only the questions, one per line."},
            {"role": "user", "content": answer}
        ]
        related_raw = self.ollama.chat(self.config.model, related_prompt)
        related_questions = [q.strip("- ").strip() for q in related_raw.split("\n") if q.strip()][:3]

        self.history.save_session(question, answer, selected_sources)
        return answer, selected_sources, related_questions

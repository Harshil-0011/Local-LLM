from .ollama_client import OllamaClient
from .history import HistoryManager
from .documents import DocumentManager
from .search import SearchEngine
import local_perplex.local_perplex_core as cpp_core

class LocalPerplex:
    def __init__(self):
        self.search_engine = SearchEngine()
        self.cpp_engine = cpp_core.ResearchEngine()
        self.ollama = OllamaClient("http://localhost:11434")
        self.history = HistoryManager()
        self.docs = DocumentManager()
        self.model = "llama3.2:8b"

    def ask(self, question: str, mode: str = "industry_standard", history: list = None):
        if history is None: history = []

        # 1. Search Web (Fast Scrape)
        raw_web_sources = self.search_engine.search(question, num_results=20)

        # 2. C++ High-Performance Ranking
        ranked_sources = self.cpp_engine.rank_sources(question, [
            {"title": s["title"], "url": s["url"], "content": s["content"]}
            for s in raw_web_sources
        ])

        # 3. Select sources
        limit = 10 if mode == "industry_standard" else 20
        selected = ranked_sources[:limit]

        # 4. Synthesize Context
        context = "\n\n".join([f"Source: {s.url}\nContent: {s.content[:2500]}" for s in selected])

        # Add local documents
        local_context = self.docs.get_local_context()
        if local_context:
            context = f"--- LOCAL DOCUMENTS ---\n{local_context}\n\n--- WEB SOURCES ---\n{context}"

        # 5. Synthesis Prompt
        system_prompt = (
            "You are a premium AI researcher. Use the provided context to answer the user's question with absolute precision. "
            "Cite sources as [URL]. If the information is missing, be honest."
        )
        if mode == "all_references":
            system_prompt += " Provide an exhaustive analysis with deep technical detail."

        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

        # 6. Generate Answer & Related
        answer = self.ollama.chat(self.model, messages)

        related_raw = self.ollama.chat(self.model, [
            {"role": "system", "content": "Suggest 3 follow-up research questions based on the answer. One per line."},
            {"role": "user", "content": answer}
        ])
        related = [q.strip("- ").strip() for q in related_raw.split("\n") if q.strip()][:3]

        self.history.save_session(question, answer, [{"title": s.title, "url": s.url, "relevance": s.relevance} for s in selected])
        return answer, selected, related

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

    def deep_research_step(self, question: str, mode: str = "pro"):
        """Agentic multi-step research."""
        # 1. Plan
        plan_prompt = [{"role": "system", "content": "Create a 3-step research plan for this question. One objective per line."}, {"role": "user", "content": question}]
        plan = self.ollama.chat(self.model, plan_prompt).split("\n")

        all_selected = []
        full_context = ""

        for step in plan[:3]:
            if not step.strip(): continue
            _, selected, context = self.research_step(step.strip(), mode="all_references")
            all_selected.extend(selected)
            full_context += f"\n--- STEP: {step} ---\n{context}\n"

        return question, all_selected, full_context

    def research_step(self, question: str, mode: str = "industry_standard", image_b64: str = None, focus_mode: str = "All"):
        """Perform the non-LLM synthesis steps of research."""
        vision_context = ""
        if image_b64:
            vision_prompt = [{"role": "user", "content": "Describe this image in detail.", "images": [image_b64]}]
            vision_context = self.ollama.chat(self.model, vision_prompt)
            question = f"[Image: {vision_context}] {question}"

        try:
            ref_prompt = [{"role": "system", "content": "You are an expert researcher. Convert the user question into an optimized search query. Return ONLY the string."}, {"role": "user", "content": question}]
            refined_query = self.ollama.chat(self.model, ref_prompt).strip('"')
        except: refined_query = question

        raw_web_sources = self.search_engine.search(refined_query, focus_mode=focus_mode)
        ranked = self.cpp_engine.rank_sources(refined_query, [{"title": s["title"], "url": s["url"], "content": s["content"]} for s in raw_web_sources])

        limit = 10 if mode == "industry_standard" else 20
        selected = ranked[:limit]

        context = "\n\n".join([f"Source: {s.url}\nContent: {s.content[:2500]}" for s in selected])
        local_context = self.docs.get_local_context()
        if local_context: context = f"--- LOCAL ---\n{local_context}\n\n--- WEB ---\n{context}"

        return question, selected, context

    def ask_stream(self, question: str, context: str, history: list = None, mode: str = "industry_standard"):
        system_prompt = "You are a premium AI researcher. Use the provided context to answer the user's question with absolute precision. Cite sources as [URL]."
        if mode == "all_references": system_prompt += " Provide an exhaustive analysis."

        messages = [{"role": "system", "content": system_prompt}]
        for h in (history or []):
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

        return self.ollama.chat(self.model, messages, stream=True)

    def finalize_research(self, question: str, answer: str, selected: list, tag: str = "General"):
        if tag != "[INCOGNITO]":
            self.history.save_session(question, answer, [{"title": s.title, "url": s.url, "relevance": s.relevance, "category": s.category, "snippet": s.content[:300]} for s in selected], tag=tag)

        related_raw = self.ollama.chat(self.model, [
            {"role": "system", "content": "Suggest 3 follow-up research questions based on the answer. One per line."},
            {"role": "user", "content": answer}
        ])
        return [q.strip("- ").strip() for q in related_raw.split("\n") if q.strip()][:3]

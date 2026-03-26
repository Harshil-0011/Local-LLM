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
        self.model = "llama3.2-vision"

    def deep_research_iterative(self, question: str, mode: str = "pro", focus_mode: str = "All"):
        """Yields progress steps and finally the results."""
        yield "status", "Analyzing your request and planning research steps..."

        plan_prompt = [
            {"role": "system", "content": "You are a research planner. Generate 3 distinct, specific search queries to fully answer the user's question. Output ONLY the queries, one per line."},
            {"role": "user", "content": question}
        ]
        try:
            plan_raw = self.ollama.chat(self.model, plan_prompt)
            queries = [q.strip("- ").strip() for q in plan_raw.split("\n") if q.strip()][:3]
        except:
            queries = [question]

        all_selected = []
        full_context = ""
        seen_urls = set()

        for i, query in enumerate(queries):
            yield "status", f"Searching for: {query}..."

            raw_web_sources = self.search_engine.search(query, focus_mode=focus_mode)
            # Filter duplicates
            unique_sources = []
            for s in raw_web_sources:
                if s["url"] not in seen_urls:
                    seen_urls.add(s["url"])
                    unique_sources.append(s)

            if unique_sources:
                ranked = self.cpp_engine.rank_sources(query, [{"title": s["title"], "url": s["url"], "content": s["content"]} for s in unique_sources])
                selected = ranked[:5] # Top 5 per query
                all_selected.extend(selected)

                context_chunk = "\n\n".join([f"Source: {s.url}\nContent: {s.content[:2000]}" for s in selected])
                full_context += f"\n--- RESEARCH SEGMENT {i+1}: {query} ---\n{context_chunk}\n"

        yield "status", "Synthesizing all gathered information..."

        local_context = self.docs.get_local_context()
        if local_context:
            full_context = f"--- LOCAL DOCUMENTS ---\n{local_context}\n\n{full_context}"

        yield "result", (question, all_selected, full_context)

    def research_step(self, question: str, mode: str = "industry_standard", image_b64: str = None, focus_mode: str = "All"):
        """Perform the non-LLM synthesis steps of research."""
        vision_context = ""
        if image_b64:
            # Enhanced "Lens" Prompt for Multimodal & Multilingual understanding
            lens_prompt = [
                {
                    "role": "user",
                    "content": f"Analyze this image in the context of: '{question}'. \n\n"
                               "1. Describe visual objects and entities.\n"
                               "2. Extract and TRANSLATE all visible text into English.\n"
                               "3. Synthesize a combined research objective from both the image and the text query.\n"
                               "Return a detailed research summary.",
                    "images": [image_b64]
                }
            ]
            vision_context = self.ollama.chat(self.model, lens_prompt)
            question = f"[Image Lens: {vision_context}] {question}"

        try:
            ref_prompt = [
                {"role": "system", "content": "You are an expert researcher. Convert the user's multimodal input into an optimized, specific search query for the web. Return ONLY the search query string."},
                {"role": "user", "content": question}
            ]
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

    def ask_stream(self, question: str, context: str, history: list = None, mode: str = "industry_standard", sources: list = None):
        system_prompt = "You are a premium AI researcher and polyglot translator. Use the provided context to answer the user's question with absolute precision. "

        if sources:
            source_map = "\n".join([f"[{i+1}] {s.url} - {s.title}" for i, s in enumerate(sources)])
            system_prompt += f"Cite sources using numerical markers like [1], [2], etc. corresponding to these sources:\n{source_map}\n"
        else:
            system_prompt += "Cite sources as [URL]."

        system_prompt += " If the user query or image contains a foreign language, translate and explain it as part of your answer."

        if mode == "all_references" or mode == "pro":
            system_prompt += " Provide an exhaustive, detailed analysis with multiple sections."

        messages = [{"role": "system", "content": system_prompt}]
        for h in (history or []):
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

        return self.ollama.chat(self.model, messages, stream=True)

    def ask(self, question: str, context: str, history: list = None, mode: str = "industry_standard") -> str:
        """Synchronous version of ask_stream for CLI and simpler use cases."""
        answer = ""
        for chunk in self.ask_stream(question, context, history, mode):
            answer += chunk
        return answer

    def finalize_research(self, question: str, answer: str, selected: list, tag: str = "General"):
        if tag != "[INCOGNITO]":
            self.history.save_session(question, answer, [{"title": s.title, "url": s.url, "relevance": s.relevance, "category": s.category, "snippet": s.content[:300]} for s in selected], tag=tag)

        related_raw = self.ollama.chat(self.model, [
            {"role": "system", "content": "Suggest 3 follow-up research questions based on the answer. One per line."},
            {"role": "user", "content": answer}
        ])
        return [q.strip("- ").strip() for q in related_raw.split("\n") if q.strip()][:3]

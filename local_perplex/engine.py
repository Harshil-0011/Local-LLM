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

    def ask(self, question: str, mode: str = "industry_standard", history: list = None, image_b64: str = None):
        if history is None: history = []

        vision_context = ""
        if image_b64:
            # Use a vision-capable model (like llava or llama3-vision) if available
            vision_prompt = [
                {
                    "role": "user",
                    "content": "Describe this image in detail for a research context.",
                    "images": [image_b64]
                }
            ]
            # We assume the same model or a specific vision model handles this
            vision_context = self.ollama.chat(self.model, vision_prompt)
            question = f"[Image Description: {vision_context}] {question}"

        # 1. AI-Driven Query Refinement
        # Note: If the refinement model fails or returns empty, we use the original question.
        try:
            refinement_prompt = [
                {"role": "system", "content": "You are a research assistant. Convert the user question into an optimized search query for DuckDuckGo. Return ONLY the search string."},
                {"role": "user", "content": question}
            ]
            refined_query = self.ollama.chat(self.model, refinement_prompt).strip('"').strip()
        except:
            refined_query = question

        if not refined_query or len(refined_query) < 2:
            refined_query = question

        # 2. Search Web (Fast Scrape)
        raw_web_sources = []
        try:
            raw_web_sources = self.search_engine.search(refined_query, num_results=20)
        except Exception as e:
            print(f"Web search failed: {e}")

        # 3. C++ High-Performance Ranking
        ranked_sources = []
        if raw_web_sources:
            try:
                ranked_sources = self.cpp_engine.rank_sources(refined_query, [
                    {"title": s["title"], "url": s["url"], "content": s["content"]}
                    for s in raw_web_sources
                ])
            except Exception as e:
                print(f"Ranking failed: {e}")

        # 4. LLM-Based Source Filtering (Better Site selection)
        # Fallback to pure C++ ranking if filtering is unreliable
        limit = 10 if mode == "industry_standard" else 20
        selected = ranked_sources[:limit]

        try:
            filter_prompt = [
                {"role": "system", "content": "Pick the most credible and relevant sources from the list for the research question. Return only the URLs, one per line."},
                {"role": "user", "content": f"Question: {question}\nSources:\n" + "\n".join([f"{s.title} ({s.url})" for s in ranked_sources[:15]])}
            ]
            best_urls_raw = self.ollama.chat(self.model, filter_prompt)
            best_urls = [u.strip() for u in best_urls_raw.split("\n") if u.strip()]

            if best_urls:
                llm_selected = []
                for s in ranked_sources:
                    if any(u in s.url for u in best_urls):
                        llm_selected.append(s)
                if llm_selected:
                    selected = llm_selected
        except:
            pass

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

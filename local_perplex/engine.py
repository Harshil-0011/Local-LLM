from .ollama_client import OllamaClient
from .history import HistoryManager
from .documents import DocumentManager
from .search import SearchEngine
from .graph import KnowledgeGraph
from .local_perplex_core import ResearchEngine
import logging

logger = logging.getLogger(__name__)

class LocalPerplex:
    def __init__(self):
        self.search_engine = SearchEngine()
        self.ranking_engine = ResearchEngine()
        self.ollama = OllamaClient("http://localhost:11434")
        self.ollama_online = False
        self.available_models = []
        self.history = HistoryManager()
        self.docs = DocumentManager()
        self.graph = KnowledgeGraph()
        self.model = "llama3.2-vision"
        
        # Try to connect to Ollama and validate models
        self._validate_ollama_connection()

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
        except Exception:
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
                ranked = self._rank_sources(query, [{"title": s["title"], "url": s["url"], "content": s["content"]} for s in unique_sources])
                selected = ranked[:5] # Top 5 per query
                all_selected.extend(selected)

                context_chunk = "\n\n".join([f"Source: {s.url}\nContent: {s.content[:2000]}" for s in selected])
                full_context += f"\n--- RESEARCH SEGMENT {i+1}: {query} ---\n{context_chunk}\n"

        yield "status", "Synthesizing all gathered information..."

        local_context = self.docs.get_local_context()
        if local_context:
            full_context = f"--- LOCAL DOCUMENTS ---\n{local_context}\n\n{full_context}"

        graph_context = self.graph.context_for_query(question)
        if graph_context:
            full_context = f"{graph_context}\n\n{full_context}"

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
        except Exception:
            refined_query = question

        raw_web_sources = self.search_engine.search(refined_query, focus_mode=focus_mode)
        ranked = self._rank_sources(refined_query, [{"title": s["title"], "url": s["url"], "content": s["content"]} for s in raw_web_sources])

        limit = 10 if mode == "industry_standard" else 20
        selected = ranked[:limit]

        context = "\n\n".join([f"Source: {s.url}\nContent: {s.content[:2500]}" for s in selected])
        local_context = self.docs.get_local_context()
        if local_context: context = f"--- LOCAL ---\n{local_context}\n\n--- WEB ---\n{context}"
        graph_context = self.graph.context_for_query(question)
        if graph_context:
            context = f"{graph_context}\n\n{context}"

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

    def _rank_sources(self, query: str, sources: list):
        """Rank sources using the pure-Python ranking engine."""
        return self.ranking_engine.rank_sources(query, sources)

    def _validate_ollama_connection(self, timeout: float = 0.75):
        """Check if Ollama is running and validate model availability."""
        try:
            import requests
            response = requests.get(f"{self.ollama.base_url}/api/tags", timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [m.get("name", "") for m in data.get("models", [])]
                self.ollama_online = True
                
                # Check if requested model is available
                if self.model not in self.available_models:
                    if self.available_models:
                        logger.warning(f"Model '{self.model}' not found. Available models: {', '.join(self.available_models)}")
                        # Use first available model as fallback
                        self.model = self.available_models[0]
                        logger.info(f"Using fallback model: {self.model}")
                    else:
                        logger.warning("No models available on Ollama. Please pull a model first.")
                        self.ollama_online = False
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
                self.ollama_online = False
                self.available_models = []
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}. App will start but research features disabled.")
            self.ollama_online = False
            self.available_models = []

    def refresh_status(self):
        self._validate_ollama_connection()
        return {
            "ollama_online": self.ollama_online,
            "available_models": self.available_models,
            "current_model": self.model,
        }

    def graph_stats(self):
        return self.graph.stats()

    def index_document(self, filename: str):
        path = self.docs.doc_dir / filename
        content = self.docs.extract_document_text(path)
        if content:
            self.graph.record_document(filename, content)

    @staticmethod
    def _source_payload(source):
        if isinstance(source, dict):
            return {
                "title": source.get("title", "Unknown"),
                "url": source.get("url", ""),
                "relevance": source.get("relevance", 0.0),
                "category": source.get("category", "General"),
                "snippet": source.get("content", source.get("snippet", ""))[:300],
            }
        return {
            "title": getattr(source, "title", "Unknown"),
            "url": getattr(source, "url", ""),
            "relevance": getattr(source, "relevance", 0.0),
            "category": getattr(source, "category", "General"),
            "snippet": getattr(source, "content", "")[:300],
        }

    def finalize_research(self, question: str, answer: str, selected: list, tag: str = "General"):
        if tag != "[INCOGNITO]":
            source_payloads = [self._source_payload(s) for s in selected]
            self.history.save_session(question, answer, source_payloads, tag=tag)
            self.graph.record_research(question, answer, selected, tag=tag)

        if not self.ollama_online:
            return ["Enable Ollama to get follow-up questions."]

        try:
            related_raw = self.ollama.chat(self.model, [
                {"role": "system", "content": "Suggest 3 follow-up research questions based on the answer. One per line."},
                {"role": "user", "content": answer}
            ])
            return [q.strip("- ").strip() for q in related_raw.split("\n") if q.strip()][:3]
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return ["Error generating follow-up questions. Check Ollama connection."]

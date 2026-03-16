import json
from pathlib import Path
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import ell
from .ollama_client import OllamaClient
from .config import get_config

# Initialize ell
ell.init(store='./logs/ell_logs', autocommit=True)

def generate_answer_with_ell(question: str, context: str, mode: str):
    """You are a helpful assistant. Use the following sources to answer the user's question. Show your references."""
    mode_inst = "Focus on industry standard practices." if mode == "industry_standard" else "Include all references and deep details."
    return f"Mode: {mode_inst}\n\nSources:\n{context}\n\nQuestion: {question}"

class PerplexityService:
    def __init__(self):
        self.config = get_config()
        self.client = OllamaClient(self.config.ollama_base_url)

    def search_and_read(self, query: str, num_sources: int = 20, mode: str = "industry_standard"):
        """
        Search for query, find sources, and read them.
        mode: 'industry_standard' or 'all_references'
        """
        sources = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_sources))
            for r in results:
                url = r['href']
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        sources.append({
                            "title": r['title'],
                            "url": url,
                            "content": text[:5000] # Limit content size
                        })
                except Exception:
                    continue
        return sources

    def answer_question(self, question: str, sources: list, mode: str = "industry_standard"):
        context = "\n\n".join([f"Source: {s['url']}\nContent: {s['content']}" for s in sources])

        # Using ell-style prompting (though we still route through our Ollama client for local execution consistency)
        # In a real ell setup, we would configure ell to use Ollama as a provider.
        # For this implementation, we'll stick to our client but structure the prompt via the ell-decorated function.

        prompt = generate_answer_with_ell(question, context, mode)

        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use the following sources to answer the user's question. Show your references."},
            {"role": "user", "content": prompt}
        ]

        return self.client.chat(self.config.planner_model, messages)

def get_future_llm_answer():
    service = PerplexityService()
    question = "Where do you think LLM will move towards in future please??"
    # For demonstration, we use a smaller number of sources to avoid massive load in this environment
    sources = service.search_and_read(question, num_sources=5)
    answer = service.answer_question(question, sources)
    return answer

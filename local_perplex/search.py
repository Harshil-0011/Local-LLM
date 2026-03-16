from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import local_perplex.local_perplex_core as core

class SearchEngine:
    def search(self, query: str, num_results: int = 20):
        sources = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            for r in results:
                url = r['href']
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        score = core.calculate_relevance(query, text)
                        sources.append({
                            "title": r['title'],
                            "url": url,
                            "content": text[:10000],
                            "relevance": score
                        })
                except Exception:
                    continue

        # Sort by relevance using C++ core scores
        sources.sort(key=lambda x: x['relevance'], reverse=True)
        return sources

from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import local_perplex.local_perplex_core as core
from concurrent.futures import ThreadPoolExecutor

class SearchEngine:
    def _scrape_url(self, r, query):
        url = r['href']
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                score = core.calculate_score(query, text)
                return {
                    "title": r['title'],
                    "url": url,
                    "content": text[:10000],
                    "relevance": score
                }
        except Exception:
            pass
        return None

    def search(self, query: str, num_results: int = 20):
        sources = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_url = {executor.submit(self._scrape_url, r, query): r for r in results}
                for future in future_to_url:
                    result = future.result()
                    if result:
                        sources.append(result)

        # Sort by relevance using C++ core scores
        sources.sort(key=lambda x: x['relevance'], reverse=True)
        return sources

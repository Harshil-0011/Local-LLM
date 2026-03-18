from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import local_perplex.local_perplex_core as core
from concurrent.futures import ThreadPoolExecutor
import time

class SearchEngine:
    def _scrape_url(self, r, query):
        url = r.get('href')
        if not url: return None
        try:
            resp = requests.get(url, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=' ', strip=True)
                score = core.calculate_score(query, text)
                return {
                    "title": r.get('title', 'No Title'),
                    "url": url,
                    "content": text[:10000],
                    "relevance": score
                }
        except Exception:
            pass
        return None

    def search(self, query: str, num_results: int = 20, focus_mode: str = "All"):
        sources = []
        results = []

        # Decorate query based on focus mode
        if focus_mode == "Academic":
            query = f"{query} site:arxiv.org OR site:scholar.google.com OR site:researchgate.net"
        elif focus_mode == "Reddit":
            query = f"{query} site:reddit.com"
        elif focus_mode == "YouTube":
            query = f"{query} site:youtube.com"
        elif focus_mode == "Technical":
            query = f"{query} site:github.com OR site:stackoverflow.com OR site:docs.microsoft.com"
        elif focus_mode == "Writing":
            num_results = 0 # No search needed for pure writing mode
        elif focus_mode == "Computational":
            query = f"{query} site:wolframalpha.com OR site:wikipedia.org"

        # Try multiple times or fallback
        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=num_results))
                if results: break
            except Exception as e:
                print(f"Search attempt {attempt+1} failed: {e}")
                time.sleep(1)

        if not results:
            return []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self._scrape_url, r, query): r for r in results}
            for future in future_to_url:
                try:
                    result = future.result()
                    if result:
                        sources.append(result)
                except:
                    continue

        sources.sort(key=lambda x: x['relevance'], reverse=True)
        return sources

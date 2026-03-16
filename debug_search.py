from duckduckgo_search import DDGS

def test():
    with DDGS() as ddgs:
        # Try a very specific query
        query = "how do LLM work?"
        results = list(ddgs.text(query, max_results=5))
        print(f"Results for '{query}':")
        for r in results:
            print(f"- {r['title']} ({r['href']})")

if __name__ == "__main__":
    test()

from duckduckgo_search import DDGS

def test():
    print("Testing duckduckgo_search.DDGS...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("how do LLM work?", max_results=5))
            print(f"Found {len(results)} results")
            for r in results:
                print(f"- {r['title']}")
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    test()

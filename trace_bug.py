import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from local_perplex.search import SearchEngine
from local_perplex.ollama_client import OllamaClient
import local_perplex.local_perplex_core as cpp_core

def debug_pipeline():
    print("--- DEBUG PIPELINE ---")
    question = "how do LLM work?"
    print(f"Original Question: {question}")

    # 1. Search
    search_engine = SearchEngine()
    print("Searching...")
    raw_sources = search_engine.search(question, num_results=5)
    print(f"Raw sources found: {len(raw_sources)}")
    for s in raw_sources:
        print(f" - {s['title']} ({s['url']})")

    if not raw_sources:
        print("CRITICAL: No raw sources found!")
        return

    # 2. C++ Ranking
    print("\nRanking with C++...")
    try:
        cpp_engine = cpp_core.ResearchEngine()
        ranked = cpp_engine.rank_sources(question, [
            {"title": s["title"], "url": s["url"], "content": s["content"]}
            for s in raw_sources
        ])
        print(f"Ranked sources: {len(ranked)}")
        for s in ranked:
            print(f" - {s.title} (Score: {s.relevance:.4f})")
    except Exception as e:
        print(f"CRITICAL: C++ ranking failed: {e}")
        return

    print("--- DEBUG END ---")

if __name__ == "__main__":
    # Ensure C++ core is built
    os.system("mkdir -p build && cd build && cmake .. && make && cd ..")
    os.system("cp build/local_perplex_core*.so local_perplex/local_perplex_core.so")
    debug_pipeline()

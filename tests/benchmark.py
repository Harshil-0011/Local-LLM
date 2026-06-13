import time
import math
import random
import string
import local_perplex.local_perplex_core as py_core

def python_tokenize(text):
    return py_core.tokenize(text)

def python_calculate_relevance(query, content):
    q_tokens = python_tokenize(query)
    c_tokens = python_tokenize(content)
    if not q_tokens or not c_tokens:
        return 0.0

    c_freq = {}
    for t in c_tokens:
        c_freq[t] = c_freq.get(t, 0) + 1

    score = 0.0
    for qt in q_tokens:
        if qt in c_freq:
            score += (1.0 + math.log(c_freq[qt]))

    return score / math.log(1.0 + len(c_tokens))

def run_benchmark():
    # Generate 10,000 dummy documents
    query = "performance of pure python local ranking code"
    docs = []
    for i in range(10000):
        content = " ".join(["".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8))) for _ in range(500)])
        # Inject some query terms
        if i % 10 == 0:
            content += " performance pure python local ranking code"
        docs.append({
            "title": f"Doc {i}",
            "url": f"http://example.com/{i}.edu",
            "content": content
        })

    print(f"--- Latency Benchmark: 10000 Documents ---")

    # Python Benchmark
    start = time.perf_counter()
    py_results = []
    for d in docs:
        score = python_calculate_relevance(query, d["content"])
        category = "Academic" if ".edu" in d["url"] else "General"
        if category == "Academic": score *= 1.25
        py_results.append(score)
    py_results.sort(reverse=True)
    py_duration = (time.perf_counter() - start) * 1000
    print(f"Python Ranking Latency (End-to-End): {py_duration:.2f} ms")

    # Package ranking engine benchmark
    engine = py_core.ResearchEngine()
    engine.rank_sources(query, docs[:10])

    start = time.perf_counter()
    ranked_results = engine.rank_sources(query, docs)
    ranked_duration = (time.perf_counter() - start) * 1000
    print(f"Package Ranking Latency: {ranked_duration:.2f} ms")
    print(f"Ranked Sources: {len(ranked_results)}")

if __name__ == "__main__":
    run_benchmark()

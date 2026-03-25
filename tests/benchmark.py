import time
import math
import random
import string
import local_perplex.local_perplex_core as cpp_core

def python_tokenize(text):
    tokens = []
    # Using C++ tokenizer for direct comparison of logic
    return cpp_core.tokenize(text)

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
    # Generate 1000 dummy documents
    query = "performance of native c++ versus interpreted python code"
    docs = []
    for i in range(10000):
        content = " ".join(["".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8))) for _ in range(500)])
        # Inject some query terms
        if i % 10 == 0:
            content += " performance native c++ python code"
        docs.append({
            "title": f"Doc {i}",
            "url": f"http://example.com/{i}.edu",
            "content": content
        })

    print(f"--- Latency Benchmark: 1000 Documents ---")

    # Python Benchmark
    start = time.perf_counter()
    py_results = []
    for d in docs:
        # Use C++ tokenize to isolate TF-IDF logic if possible,
        # or just keep it as is to show end-to-end Python vs C++
        score = python_calculate_relevance(query, d["content"])
        category = "Academic" if ".edu" in d["url"] else "General"
        if category == "Academic": score *= 1.25
        py_results.append(score)
    py_results.sort(reverse=True)
    py_duration = (time.perf_counter() - start) * 1000
    print(f"Python Ranking Latency (End-to-End): {py_duration:.2f} ms")

    # C++ Benchmark (Warm-up)
    engine = cpp_core.ResearchEngine()
    engine.rank_sources(query, docs[:10])

    start = time.perf_counter()
    cpp_results = engine.rank_sources(query, docs)
    cpp_duration = (time.perf_counter() - start) * 1000
    print(f"C++ Core Ranking Latency: {cpp_duration:.2f} ms")

    print(f"Performance Gain: {py_duration / cpp_duration:.1f}x faster")

if __name__ == "__main__":
    run_benchmark()

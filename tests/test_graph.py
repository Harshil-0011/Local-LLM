from local_perplex.graph import KnowledgeGraph


def test_graph_records_research_and_recalls_context(tmp_path):
    graph = KnowledgeGraph(db_path=tmp_path / "graph.sqlite3")

    graph.record_research(
        "How does Python graph memory work?",
        "Python graph memory stores research as nodes and weighted edges.",
        [
            {
                "title": "Graph Memory Notes",
                "url": "https://example.com/graph",
                "content": "A graph connects questions, answers, sources, and documents.",
            }
        ],
        tag="Tests",
    )

    stats = graph.stats()
    context = graph.context_for_query("python graph memory")

    assert stats["nodes"] > 0
    assert stats["edges"] > 0
    assert "Related past research" in context
    assert "Python graph memory" in context


def test_graph_records_documents(tmp_path):
    graph = KnowledgeGraph(db_path=tmp_path / "graph.sqlite3")

    graph.record_document("notes.md", "Vector retrieval and graph memory can improve local answers.")
    context = graph.context_for_query("graph retrieval")

    assert "Related local documents" in context
    assert "notes.md" in context

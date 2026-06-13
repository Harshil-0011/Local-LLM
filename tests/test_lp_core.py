import unittest
import local_perplex.local_perplex_core as core

class TestCore(unittest.TestCase):
    def test_relevance(self):
        query = "artificial intelligence"
        content = "Artificial intelligence is a branch of computer science."
        score = core.calculate_score(query, content)
        self.assertGreater(score, 0)

    def test_tokenize(self):
        text = "Hello, World!"
        tokens = core.tokenize(text)
        self.assertEqual(tokens, ["hello", "world"])

    def test_rank_sources(self):
        engine = core.ResearchEngine()
        ranked = engine.rank_sources("python graph memory", [
            {"title": "Cooking", "url": "https://example.com/food", "content": "bread and soup"},
            {"title": "Python Graph Memory", "url": "https://example.com/python", "content": "python graph memory stores nodes"},
        ])
        self.assertEqual(ranked[0].title, "Python Graph Memory")
        self.assertGreater(ranked[0].relevance, ranked[1].relevance)

if __name__ == "__main__":
    unittest.main()

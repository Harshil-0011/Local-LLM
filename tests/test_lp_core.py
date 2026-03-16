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

if __name__ == "__main__":
    unittest.main()

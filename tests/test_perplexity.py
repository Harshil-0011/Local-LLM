from project_wizard.perplexity import PerplexityService, get_future_llm_answer
import unittest
from unittest.mock import patch

class TestPerplexity(unittest.TestCase):
    @patch('project_wizard.perplexity.DDGS')
    @patch('project_wizard.perplexity.requests.get')
    @patch('project_wizard.ollama_client.OllamaClient.chat')
    def test_perplexity_flow(self, mock_chat, mock_get, mock_ddgs):
        # Mock DDGS
        mock_ddgs_instance = mock_ddgs.return_value.__enter__.return_value
        mock_ddgs_instance.text.return_value = [{'href': 'http://test.com', 'title': 'Test'}]

        # Mock requests
        mock_resp = patch('requests.Response').start()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body>Some content</body></html>"
        mock_get.return_value = mock_resp

        # Mock Ollama
        mock_chat.return_value = "The future of LLM is bright."

        from project_wizard.perplexity import PerplexityService
        svc = PerplexityService()
        sources = svc.search_and_read("test", num_sources=1)
        answer = svc.answer_question("test", sources)

        self.assertEqual(answer, "The future of LLM is bright.")
        self.assertEqual(len(sources), 1)

if __name__ == '__main__':
    unittest.main()

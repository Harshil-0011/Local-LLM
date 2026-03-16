import unittest
from unittest.mock import patch, MagicMock
from project_wizard.ollama_client import OllamaClient

class TestOllamaClient(unittest.TestCase):
    @patch('requests.post')
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "Hello world"}}
        mock_post.return_value = mock_response

        client = OllamaClient("http://localhost:11434")
        response = client.chat("llama3", [{"role": "user", "content": "hi"}])

        self.assertEqual(response, "Hello world")
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_chat_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection error")

        client = OllamaClient("http://localhost:11434")
        with self.assertRaises(RuntimeError):
            client.chat("llama3", [{"role": "user", "content": "hi"}])

if __name__ == '__main__':
    unittest.main()

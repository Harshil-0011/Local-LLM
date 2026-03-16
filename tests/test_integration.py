import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import json
import os

from project_wizard.interview.manager import InterviewManager
from project_wizard.spec.builder import SpecBuilder
from project_wizard.codegen.generator import CodeGenerator
from project_wizard.config import Config

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = Path("integration_test_output")
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)
        self.test_output_dir.mkdir()

        self.config = Config(
            ollama_base_url="http://mocked:11434",
            planner_model="planner-mock",
            coder_model="coder-mock",
            default_output_dir=str(self.test_output_dir)
        )

    def tearDown(self):
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    @patch('project_wizard.ollama_client.requests.post')
    def test_full_pipeline(self, mock_post):
        # 1. Mock Ollama responses
        def mock_ollama_side_effect(url, json=None, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200

            if "api/chat" in url:
                model = json.get("model")
                if model == "planner-mock":
                    content = "# Project Specification\n\nThis is a mock spec."
                elif model == "coder-mock":
                    content = """
<file name="main.py">
print("Integrated!")
</file>
<file name="README.md">
# Mock Project
</file>
"""
                else:
                    content = "Unknown model"

                mock_resp.json.return_value = {"message": {"content": content}}
            return mock_resp

        mock_post.side_effect = mock_ollama_side_effect

        # 2. Step 1: Interview
        manager = InterviewManager(self.test_output_dir)
        manager.update_answer("project_name", "test_project")
        manager.update_answer("description", "A test project for integration.")
        self.assertTrue((self.test_output_dir / "answers.json").exists())

        # 3. Step 2: Build Spec
        builder = SpecBuilder(self.config.ollama_base_url, self.config.planner_model)
        spec_content = builder.build_spec(manager.answers)
        spec_file = builder.save_spec(self.test_output_dir, spec_content)
        self.assertTrue(spec_file.exists())
        self.assertIn("# Project Specification", spec_content)

        # 4. Step 3: Generate Code
        generator = CodeGenerator(self.config.ollama_base_url, self.config.coder_model)
        llm_output = generator.generate_code(spec_content)
        generator.parse_and_save(self.test_output_dir, llm_output)

        # 5. Verify results
        self.assertTrue((self.test_output_dir / "main.py").exists())
        self.assertTrue((self.test_output_dir / "README.md").exists())

        with open(self.test_output_dir / "main.py", "r") as f:
            self.assertEqual(f.read().strip(), 'print("Integrated!")')

if __name__ == '__main__':
    unittest.main()

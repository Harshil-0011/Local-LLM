import unittest
from pathlib import Path
import os
import shutil
from project_wizard.codegen.generator import CodeGenerator

class TestCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_output")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_parse_and_save(self):
        llm_output = """
Some text here.
<file name="main.py">
print("hello")
</file>
<file name="utils/helper.py">
def help(): pass
</file>
"""
        generator = CodeGenerator("http://localhost:11434", "test-model")
        generator.parse_and_save(self.test_dir, llm_output)

        main_py = self.test_dir / "main.py"
        helper_py = self.test_dir / "utils" / "helper.py"

        self.assertTrue(main_py.exists())
        self.assertTrue(helper_py.exists())

        with open(main_py, "r") as f:
            self.assertEqual(f.read().strip(), 'print("hello")')

if __name__ == '__main__':
    unittest.main()

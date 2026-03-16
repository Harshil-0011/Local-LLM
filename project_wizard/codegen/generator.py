import re
import os
from pathlib import Path
from ..ollama_client import ollama_chat

CODEGEN_SYSTEM_PROMPT = """You are an expert programmer.
Your task is to generate a complete project based on the provided specification.
Return the code for all files in the following format:

<file name="path/to/file.ext">
// file content
</file>

Ensure the code is compilable/runnable on Windows.
Include all necessary configuration files (e.g., pyproject.toml, CMakeLists.txt, README.md).
"""

class CodeGenerator:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def generate_code(self, spec_content: str) -> str:
        user_content = f"Here is the project specification:\n\n{spec_content}\n\nPlease generate the full project files."

        messages = [
            {"role": "system", "content": CODEGEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        return ollama_chat(self.base_url, self.model, messages)

    def parse_and_save(self, output_dir: Path, llm_output: str, dry_run: bool = False):
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = output_dir.resolve()

        # Pattern to match <file name="...">content</file>
        pattern = re.compile(r'<file\s+name=["\'](.*?)["\']\s*>(.*?)</file>', re.DOTALL)
        matches = pattern.findall(llm_output)

        for file_path_str, content in matches:
            # Basic path traversal prevention
            safe_path_str = file_path_str.strip().replace('\\', '/').lstrip('/')
            file_path = (output_dir / safe_path_str).resolve()

            if not str(file_path).startswith(str(output_dir)):
                print(f"Warning: Skipping unsafe path: {file_path_str}")
                continue

            if dry_run:
                print(f"Dry-run: Would generate {file_path}")
                continue

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())

            print(f"Generated: {file_path_str}")

        if not matches:
             print("Warning: No file blocks found in LLM output.")

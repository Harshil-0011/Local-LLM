import json
from pathlib import Path
from ..ollama_client import ollama_chat

SPEC_SYSTEM_PROMPT = """You are a senior software architect.
Your task is to convert project interview answers into a detailed project specification.
Provide a structured specification in Markdown including:
- Overview and goals.
- Detailed architecture (layers, components).
- Data flow description.
- Modules, classes, and functions with responsibilities.
- File and directory layout proposal.
- Error handling and logging strategy.
- Testing strategy.
- Language-specific notes for the chosen languages.
"""

class SpecBuilder:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def build_spec(self, answers: dict) -> str:
        user_content = f"Here are the project interview answers in JSON format:\n\n{json.dumps(answers, indent=2)}\n\nPlease generate a detailed project specification."

        messages = [
            {"role": "system", "content": SPEC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        spec_content = ollama_chat(self.base_url, self.model, messages)
        return spec_content

    def save_spec(self, output_dir: Path, spec_content: str):
        output_dir.mkdir(parents=True, exist_ok=True)
        spec_file = output_dir / "project_spec.md"
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(spec_content)
        return spec_file

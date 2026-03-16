import json
from pathlib import Path
from typing import Any, Dict, List

QUESTIONS = [
    {"id": "project_name", "text": "Project name", "default": "my_awesome_project"},
    {"id": "description", "text": "Short description", "default": "A new project."},
    {"id": "languages", "text": "Target languages (Python, C, C++)", "default": "Python"},
    {"id": "target_os", "text": "Target OS (e.g., Windows, Cross-platform)", "default": "Windows"},
    {"id": "app_type", "text": "Type of application (CLI, GUI, web, service, etc.)", "default": "CLI"},
    {"id": "features", "text": "Main features and use cases", "default": ""},
    {"id": "performance", "text": "Performance constraints (latency, throughput, memory)", "default": "None"},
    {"id": "hardware", "text": "Hardware assumptions (CPU-only, GPU available, approximate RAM)", "default": "CPU-only"},
    {"id": "dependencies", "text": "Dependencies/frameworks (Qt, SDL, Boost, Flask, etc.)", "default": "None"},
    {"id": "data_storage", "text": "Data storage (files, DB, JSON/CSV/SQL)", "default": "Files"},
    {"id": "config_needs", "text": "Configuration needs (config files, env vars, CLI flags)", "default": "Config files"},
    {"id": "logging", "text": "Logging and monitoring requirements", "default": "Basic console logging"},
    {"id": "error_handling", "text": "Error-handling expectations (strict, fail-fast, graceful)", "default": "Graceful"},
    {"id": "testing", "text": "Testing requirements (unit, integration, smoke tests)", "default": "Unit tests"},
]

class InterviewManager:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.answers_file = output_dir / "answers.json"
        self.answers: Dict[str, Any] = {}
        self.load_answers()

    def load_answers(self):
        if self.answers_file.exists():
            with open(self.answers_file, "r") as f:
                self.answers = json.load(f)

    def save_answers(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.answers_file, "w") as f:
            json.dump(self.answers, f, indent=2)

    def update_answer(self, question_id: str, answer: Any):
        self.answers[question_id] = answer
        self.save_answers()

    def get_questions(self) -> List[Dict[str, str]]:
        return QUESTIONS

    def is_complete(self) -> bool:
        return all(q["id"] in self.answers for q in QUESTIONS)

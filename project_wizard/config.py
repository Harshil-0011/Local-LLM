import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_DIR = Path.home() / ".project_wizard"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"

class Config(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    planner_model: str = "llama3.2:8b"
    coder_model: str = "deepseek-coder:latest"
    default_output_dir: str = str(Path.cwd() / "generated_projects")
    default_language_preferences: list[str] = ["Python"]

    model_config = SettingsConfigDict(env_prefix="WIZARD_")

    @classmethod
    def load(cls, config_path: Path | None = None):
        path = config_path or DEFAULT_CONFIG_PATH
        data = {}
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}

        return cls(**data)

    def save(self, config_path: Path | None = None):
        path = config_path or DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f)

def get_config(config_path: str | None = None) -> Config:
    path = Path(config_path) if config_path else None
    return Config.load(path)

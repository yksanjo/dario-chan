"""Dario-chan configuration."""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # LLM settings
    model: str = os.getenv("DARIO_MODEL", "qwen2.5:0.5b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature: float = 0.7
    max_context: int = 4096

    # Buddy settings
    buddy_enabled: bool = True
    buddy_species: str | None = None  # Auto-generate from user ID if None

    # Paths
    data_dir: str = os.path.expanduser("~/.dario-chan")
    history_file: str = "history.json"
    buddy_file: str = "buddy.json"

    # Tool settings
    allowed_tools: list[str] = field(
        default_factory=lambda: ["bash", "file_read", "file_write", "file_edit", "grep", "web_search"]
    )
    sandbox_mode: bool = False

    @property
    def history_path(self) -> str:
        return os.path.join(self.data_dir, self.history_file)

    @property
    def buddy_path(self) -> str:
        return os.path.join(self.data_dir, self.buddy_file)

    def ensure_dirs(self):
        os.makedirs(self.data_dir, exist_ok=True)

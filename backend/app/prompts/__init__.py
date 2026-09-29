"""Prompts package."""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """Loads a prompt template string from app/prompts directory."""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file '{filename}' not found in {PROMPTS_DIR}")
    return filepath.read_text(encoding="utf-8")


__all__ = ["load_prompt"]

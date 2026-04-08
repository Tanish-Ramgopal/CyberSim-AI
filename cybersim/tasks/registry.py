from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _tasks_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "tasks"


def available_tasks() -> List[str]:
    names: List[str] = []
    for file in sorted(_tasks_dir().glob("*.json")):
        names.append(file.stem)
    return names


def load_task(task_name: str) -> Dict:
    path = _tasks_dir() / f"{task_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Task '{task_name}' not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    return config


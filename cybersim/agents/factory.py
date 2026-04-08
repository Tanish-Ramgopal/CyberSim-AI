from __future__ import annotations

from cybersim.agents.base import BaseAgent
from cybersim.agents.baseline import BaselineDefenseAgent
from cybersim.agents.unsw_model import UNSWModelDefenseAgent


def build_agent(name: str) -> BaseAgent:
    normalized = name.strip().lower()
    if normalized == "baseline":
        return BaselineDefenseAgent()
    if normalized in {"unsw_model", "model"}:
        return UNSWModelDefenseAgent()
    raise ValueError(f"Unsupported agent '{name}'. Available agents: baseline, unsw_model")


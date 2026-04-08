from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Action(BaseModel):
    action_type: Literal["block_ip", "kill_process", "isolate_machine", "raise_alert", "noop"]
    target: str = Field(default="none")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    tick: int
    max_ticks: int
    task_name: str
    recent_auth_logs: List[str]
    recent_network_logs: List[str]
    recent_process_logs: List[str]
    alerts: List[str]
    blocked_ips: List[str]
    isolated_hosts: List[str]
    active_threat: bool
    possible_threats: List[str]
    objective: str


class Reward(BaseModel):
    value: float = Field(ge=-1.0, le=1.0)
    components: Dict[str, float] = Field(default_factory=dict)
    reason: str = ""


class EvaluationResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any]
    reasoning: List[str]
    final_status: str
    first_response_tick: Optional[int]


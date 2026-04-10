from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cybersim.environment.core import SimulationEnvironment
from cybersim.models import Action
from cybersim.tasks.registry import available_tasks, load_task

app = FastAPI(title="CyberSim AI API", version="0.2.0")

_CURRENT_ENV: Optional[SimulationEnvironment] = None
_CURRENT_TASK: Optional[str] = None
_CURRENT_SEED: int = 42


class ResetRequest(BaseModel):
    task: str = Field(default="brute_force")
    seed: int = Field(default=42)


class StepRequest(BaseModel):
    action_type: str
    target: str = "none"
    metadata: Dict[str, Any] = Field(default_factory=dict)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "CyberSim AI API",
        "status": "running",
        "health": "/health",
        "tasks": "/tasks",
        "flow": ["POST /reset", "POST /step", "GET /state", "POST /close"],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def tasks() -> Dict[str, list[str]]:
    return {"tasks": available_tasks()}


@app.post("/reset")
def reset(request: ResetRequest) -> Dict[str, Any]:
    global _CURRENT_ENV, _CURRENT_TASK, _CURRENT_SEED

    if request.task not in available_tasks():
        raise HTTPException(status_code=400, detail=f"Unknown task '{request.task}'")

    task_cfg = load_task(request.task)
    _CURRENT_ENV = SimulationEnvironment(task_cfg, seed=request.seed)
    _CURRENT_TASK = request.task
    _CURRENT_SEED = request.seed
    obs = _CURRENT_ENV.reset()
    return {"task": _CURRENT_TASK, "seed": _CURRENT_SEED, "observation": obs.model_dump(), "done": False}


@app.post("/step")
def step(request: StepRequest) -> Dict[str, Any]:
    if _CURRENT_ENV is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    action = Action(action_type=request.action_type, target=request.target, metadata=request.metadata)
    obs, reward, done, info = _CURRENT_ENV.step(action)
    return {
        "task": _CURRENT_TASK,
        "seed": _CURRENT_SEED,
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state() -> Dict[str, Any]:
    if _CURRENT_ENV is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return {"task": _CURRENT_TASK, "seed": _CURRENT_SEED, "state": _CURRENT_ENV.state()}


@app.post("/close")
def close() -> Dict[str, bool]:
    global _CURRENT_ENV, _CURRENT_TASK
    if _CURRENT_ENV is not None:
        _CURRENT_ENV.close()
    _CURRENT_ENV = None
    _CURRENT_TASK = None
    return {"closed": True}


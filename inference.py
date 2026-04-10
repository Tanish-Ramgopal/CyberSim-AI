"""Judge-facing LLM runner. Terminal `score` comes from `DeterministicGrader` — see `cybersim/grader/spec.py` / README ## Grader."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import List, Optional

from openai import OpenAI

from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.models import Action, Observation
from cybersim.tasks.registry import load_task

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
TASK_NAME = os.getenv("CYBERSIM_TASK", "brute_force")
BENCHMARK = os.getenv("CYBERSIM_BENCHMARK", "cybersim-ai")
MAX_STEPS = int(os.getenv("MAX_STEPS", "32"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
SEED = int(os.getenv("SEED", "42"))
CYBERSIM_ENV_URL = os.getenv("CYBERSIM_ENV_URL")


def _single_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    done_val = str(done).lower()
    error_val = "null" if error is None else _single_line(error)
    action_val = _single_line(action)
    print(
        f"[STEP] step={step} action={action_val} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def build_user_prompt(observation: Observation) -> str:
    payload = {
        "objective": observation.objective,
        "tick": observation.tick,
        "max_ticks": observation.max_ticks,
        "possible_threats": observation.possible_threats,
        "recent_auth_logs": observation.recent_auth_logs,
        "recent_network_logs": observation.recent_network_logs,
        "recent_process_logs": observation.recent_process_logs,
        "blocked_ips": observation.blocked_ips,
        "isolated_hosts": observation.isolated_hosts,
        "allowed_actions": ["block_ip", "kill_process", "isolate_machine", "raise_alert", "noop"],
        "required_json": {"action_type": "string", "target": "string"},
    }
    return json.dumps(payload)


def get_model_action(client: Optional[OpenAI], observation: Observation) -> Action:
    if client is None:
        return Action(action_type="noop", target="none")
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a SOC defense agent. Return only JSON with keys action_type and target. "
                        "No markdown, no explanation."
                    ),
                },
                {"role": "user", "content": build_user_prompt(observation)},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        data = json.loads(text)
        return Action(action_type=data.get("action_type", "noop"), target=data.get("target", "none"))
    except Exception:
        return Action(action_type="noop", target="none")


def _http_json(method: str, url: str, payload: Optional[dict] = None) -> dict:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    task = load_task(TASK_NAME)
    env = SimulationEnvironment(task, seed=SEED) if not CYBERSIM_ENV_URL else None
    grader = DeterministicGrader()

    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    last_error: Optional[str] = None

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    client: Optional[OpenAI] = None

    try:
        # OpenAI client is the required LLM interface for evaluation runs.
        if HF_TOKEN:
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
        else:
            last_error = "missing HF_TOKEN"
        if CYBERSIM_ENV_URL:
            base = CYBERSIM_ENV_URL.rstrip("/")
            reset_data = _http_json("POST", f"{base}/reset", {"task": TASK_NAME, "seed": SEED})
            observation = Observation(**reset_data["observation"])
            done = bool(reset_data.get("done", False))
            max_ticks = int(observation.max_ticks)
        else:
            observation = env.reset()
            done = False
            max_ticks = int(env.max_ticks)
        final_metrics = {}

        for step in range(1, min(MAX_STEPS, max_ticks) + 1):
            if done:
                break

            action = get_model_action(client, observation)
            action_repr = f"{action.action_type}('{action.target}')"

            try:
                if CYBERSIM_ENV_URL:
                    step_data = _http_json(
                        "POST",
                        f"{base}/step",
                        {
                            "action_type": action.action_type,
                            "target": action.target,
                            "metadata": action.metadata,
                        },
                    )
                    observation = Observation(**step_data["observation"])
                    reward_value = float(step_data["reward"]["value"])
                    done = bool(step_data.get("done", False))
                    info = step_data.get("info", {})
                    final_metrics = info.get("metrics", {})
                    success = bool(info.get("success", False))
                else:
                    observation, reward, done, info = env.step(action)
                    reward_value = float(reward.value)
                    final_metrics = info.get("metrics", {})
                    success = bool(info.get("success", False))
                last_error = None
            except (Exception, urllib.error.URLError) as exc:
                reward_value = 0.0
                done = True
                success = False
                last_error = str(exc)

            rewards.append(reward_value)
            steps_taken = step
            log_step(step=step, action=action_repr, reward=reward_value, done=done, error=last_error)

        if final_metrics:
            score = grader.evaluate(final_metrics, success=success, max_ticks=max_ticks).score
            score = float(max(0.0, min(1.0, score)))
        else:
            score = 0.0

    finally:
        try:
            if CYBERSIM_ENV_URL:
                _http_json("POST", f"{CYBERSIM_ENV_URL.rstrip('/')}/close", {})
            else:
                env.close()
        except Exception:
            # Keep stdout contract strict: emit only START/STEP/END lines.
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()


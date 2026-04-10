"""Multi-task LLM evaluation; scores use `DeterministicGrader` — see `cybersim/grader/spec.py`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.models import Action, Observation
from cybersim.tasks.registry import available_tasks, load_task

from scripts.run_simulation import run as run_local_agent

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")


def _prompt_for_action(task_name: str, obs: Observation) -> str:
    payload = {
        "task_name": task_name,
        "tick": obs.tick,
        "max_ticks": obs.max_ticks,
        "objective": obs.objective,
        "possible_threats": obs.possible_threats,
        "recent_auth_logs": obs.recent_auth_logs,
        "recent_network_logs": obs.recent_network_logs,
        "recent_process_logs": obs.recent_process_logs,
        "allowed_actions": ["block_ip", "kill_process", "isolate_machine", "raise_alert", "noop"],
        "response_format": {"action_type": "one allowed action", "target": "string target or none"},
    }
    return json.dumps(payload)


def _parse_action(raw_text: str) -> Action:
    try:
        data = json.loads(raw_text)
        return Action(action_type=data.get("action_type", "noop"), target=data.get("target", "none"))
    except Exception:
        return Action(action_type="noop", target="none")


def _llm_action(client: OpenAI, model: str, task_name: str, obs: Observation, seed: int) -> Action:
    response = client.responses.create(
        model=model,
        seed=seed,
        temperature=0,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a SOC defender. Return only strict JSON with fields "
                    "action_type and target. Avoid markdown or extra text."
                ),
            },
            {"role": "user", "content": _prompt_for_action(task_name, obs)},
        ],
    )
    text = response.output_text.strip()
    return _parse_action(text)


def run_task(client: OpenAI, task_name: str, model: str, seed: int) -> Dict[str, Any]:
    task = load_task(task_name)
    env = SimulationEnvironment(task, seed=seed)
    grader = DeterministicGrader()

    observation = env.reset()
    done = False
    final_metrics: Dict[str, Any] = {}
    total_reward = 0.0
    success = False

    while not done:
        action = _llm_action(client, model, task_name, observation, seed)
        observation, reward, done, info = env.step(action)
        total_reward = round(total_reward + reward.value, 4)
        final_metrics = info["metrics"]
        success = info["success"]

    grade = grader.evaluate(final_metrics, success=success, max_ticks=env.max_ticks)
    return {
        "task": task_name,
        "model": model,
        "seed": seed,
        "score": grade.score,
        "episode_reward": total_reward,
        "status": grade.final_status,
        "reasoning": grade.reasoning,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpenAI baseline across CyberSim tasks.")
    parser.add_argument("--model", default=MODEL_NAME, help="OpenAI model name")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    parser.add_argument("--tasks", nargs="*", default=available_tasks(), help="Task list")
    parser.add_argument("--compare-agent", default="baseline", help="Local comparison agent")
    args = parser.parse_args()

    if not API_KEY:
        raise EnvironmentError("Set HF_TOKEN or OPENAI_API_KEY for baseline runs")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    results: List[Dict[str, Any]] = []
    baseline_results: List[Dict[str, Any]] = []
    for task in args.tasks:
        results.append(run_task(client, task, args.model, args.seed))
        baseline_results.append(
            run_local_agent(task_name=task, agent_name=args.compare_agent, seed=args.seed, max_steps=None, show_logs=False)
        )

    avg_score = round(sum(r["score"] for r in results) / len(results), 4) if results else 0.0
    by_level = {}
    for r in results:
        cfg = load_task(r["task"])
        level = cfg.get("difficulty", "unknown")
        by_level[level] = {"task": r["task"], "llm_score": r["score"]}
    for b in baseline_results:
        cfg = load_task(b["task"])
        level = cfg.get("difficulty", "unknown")
        by_level.setdefault(level, {"task": b["task"]})
        by_level[level]["baseline_score"] = b["score"]

    for level in ["easy", "medium", "hard"]:
        entry = by_level.get(level)
        if not entry:
            print(f"{level}: n/a | {args.compare_agent}: n/a")
        else:
            print(f"{level}: {entry.get('llm_score', 0.0):.4f} | {args.compare_agent}: {entry.get('baseline_score', 0.0):.4f}")
    print(
        json.dumps(
            {"results": results, "baseline_results": baseline_results, "average_score": avg_score, "scoreboard": by_level},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()


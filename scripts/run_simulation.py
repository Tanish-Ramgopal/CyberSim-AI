from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from cybersim.agents.factory import build_agent
from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.tasks.registry import available_tasks, load_task


def run(task_name: str, agent_name: str, seed: int, max_steps: int | None, show_logs: bool) -> Dict[str, Any]:
    task = load_task(task_name)
    env = SimulationEnvironment(task, seed=seed)
    agent = build_agent(agent_name)
    grader = DeterministicGrader()

    max_ticks = task["max_ticks"] if max_steps is None else min(max_steps, int(task["max_ticks"]))
    env.max_ticks = max_ticks

    observation = env.reset()
    done = False
    success = False
    final_metrics = {}
    total_reward = 0.0

    while not done:
        action = agent.act(observation)
        observation, reward, done, info = env.step(action)
        total_reward = round(total_reward + reward.value, 4)
        success = info["success"]
        final_metrics = info["metrics"]

    grade = grader.evaluate(metrics=final_metrics, success=success, max_ticks=max_ticks)
    payload = {
        "task": task_name,
        "agent": agent_name,
        "seed": seed,
        "max_ticks": max_ticks,
        "status": grade.final_status,
        "score": grade.score,
        "episode_reward": total_reward,
        "reasoning": grade.reasoning,
        "details": grade.details,
        "final_state": env.state(),
        "logs": env.export_all_logs() if show_logs else "hidden (use --show-logs)",
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CyberSim AI simulation.")
    parser.add_argument("--task", required=True, choices=available_tasks(), help="Task name from configs/tasks")
    parser.add_argument("--agent", default="baseline", help="Agent to run (default: baseline)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic replay")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional max steps override")
    parser.add_argument("--show-logs", action="store_true", help="Include all generated logs in output")
    args = parser.parse_args()

    result = run(
        task_name=args.task,
        agent_name=args.agent,
        seed=args.seed,
        max_steps=args.max_steps,
        show_logs=args.show_logs,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


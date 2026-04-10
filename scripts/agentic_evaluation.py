"""Variance checks across agents; scores from `DeterministicGrader` (`cybersim/grader/spec.py`)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.run_simulation import run

TASK_LEVELS = {
    "brute_force": "easy",
    "malware_spread": "medium",
    "data_exfiltration": "hard",
}


def evaluate_agent(agent: str, seeds: List[int]) -> Dict:
    by_task: Dict[str, List[float]] = {task: [] for task in TASK_LEVELS}
    for seed in seeds:
        for task in TASK_LEVELS:
            result = run(task_name=task, agent_name=agent, seed=seed, max_steps=None, show_logs=False)
            by_task[task].append(float(result["score"]))

    summary = {}
    for task, scores in by_task.items():
        summary[task] = {
            "difficulty": TASK_LEVELS[task],
            "scores": scores,
            "mean": round(mean(scores), 4),
            "std": round(pstdev(scores), 6),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase-2 agentic evaluation with score variance checks.")
    parser.add_argument("--seeds", nargs="*", type=int, default=[7, 11, 19, 42, 77], help="Seeds to evaluate")
    parser.add_argument("--llm-agent", default="unsw_model", help="Agent name for standard LLM/model agent")
    args = parser.parse_args()

    baseline = evaluate_agent("baseline", args.seeds)
    llm = evaluate_agent(args.llm_agent, args.seeds)

    out = {"seeds": args.seeds, "baseline": baseline, args.llm_agent: llm}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()


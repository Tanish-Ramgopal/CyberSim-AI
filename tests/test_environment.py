from __future__ import annotations

import unittest

from cybersim.agents.factory import build_agent
from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.tasks.registry import load_task


class EnvironmentDeterminismTests(unittest.TestCase):
    def run_episode(self, task_name: str, seed: int = 42) -> dict:
        task = load_task(task_name)
        env = SimulationEnvironment(task, seed=seed)
        agent = build_agent("baseline")
        grader = DeterministicGrader()

        obs = env.reset()
        done = False
        success = False
        metrics = {}
        total_reward = 0.0

        while not done:
            action = agent.act(obs)
            obs, reward, done, info = env.step(action)
            success = info["success"]
            metrics = info["metrics"]
            total_reward = round(total_reward + reward.value, 4)

        grade = grader.evaluate(metrics, success, env.max_ticks)
        return {"score": grade.score, "reward": total_reward, "metrics": metrics}

    def test_deterministic_for_same_seed(self) -> None:
        first = self.run_episode("data_exfiltration", seed=42)
        second = self.run_episode("data_exfiltration", seed=42)
        self.assertEqual(first, second)

    def test_score_range_is_normalized(self) -> None:
        result = self.run_episode("brute_force", seed=42)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)


if __name__ == "__main__":
    unittest.main()


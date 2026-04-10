"""Grader sensitivity; rubric weights in `cybersim/grader/spec.py`."""

from __future__ import annotations

import unittest

from scripts.run_simulation import run


class GraderVariationTests(unittest.TestCase):
    def test_grader_not_constant_across_agents(self) -> None:
        baseline = run("data_exfiltration", "baseline", seed=42, max_steps=None, show_logs=False)["score"]
        model = run("data_exfiltration", "unsw_model", seed=42, max_steps=None, show_logs=False)["score"]
        # Agents may tie on some tasks; require non-constant behavior across altered trajectory settings.
        weakened = run("data_exfiltration", "baseline", seed=42, max_steps=3, show_logs=False)["score"]
        self.assertTrue(len({baseline, model, weakened}) >= 2)

    def test_scores_bounded(self) -> None:
        for task in ["brute_force", "malware_spread", "data_exfiltration"]:
            score = run(task, "baseline", seed=42, max_steps=None, show_logs=False)["score"]
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()


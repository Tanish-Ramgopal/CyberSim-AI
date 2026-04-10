"""
Comprehensive test suite for validating CyberSim AI submissions.
Tests agent implementation, scoring logic, and compliance.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, List
from io import StringIO

from cybersim.agents.factory import build_agent
from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.tasks.registry import load_task, available_tasks
from cybersim.models import Action, Observation


class TestAgentCompliance(unittest.TestCase):
    """Test agent implementation compliance."""
    
    def test_baseline_agent_exists(self):
        """Test that baseline agent can be instantiated."""
        agent = build_agent("baseline")
        self.assertIsNotNone(agent)
        self.assertTrue(hasattr(agent, "act"))
    
    def test_agent_act_returns_action(self):
        """Test that agent.act() returns a valid Action."""
        agent = build_agent("baseline")
        task = load_task("brute_force")
        env = SimulationEnvironment(task, seed=42)
        observation = env.reset()
        
        action = agent.act(observation)
        self.assertIsInstance(action, Action)
        self.assertIn(action.action_type, ["block_ip", "kill_process", "isolate_machine", "raise_alert", "noop"])
        self.assertIsNotNone(action.target)


class TestEnvironmentCompliance(unittest.TestCase):
    """Test environment and observation model compliance."""
    
    def test_reset_returns_observation(self):
        """Test that env.reset() returns Observation."""
        task = load_task("brute_force")
        env = SimulationEnvironment(task, seed=42)
        obs = env.reset()
        self.assertIsInstance(obs, Observation)
    
    def test_step_returns_valid_tuple(self):
        """Test that env.step() returns (obs, reward, done, info)."""
        task = load_task("brute_force")
        env = SimulationEnvironment(task, seed=42)
        obs = env.reset()
        
        action = Action(action_type="noop", target="none")
        result = env.step(action)
        
        self.assertEqual(len(result), 4)
        obs, reward, done, info = result
        self.assertIsInstance(obs, Observation)
        self.assertIsNotNone(reward)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
        self.assertIn("success", info)
        self.assertIn("metrics", info)
    
    def test_observation_has_required_fields(self):
        """Test that Observation has all required fields."""
        task = load_task("brute_force")
        env = SimulationEnvironment(task, seed=42)
        obs = env.reset()
        
        required_fields = ["tick", "max_ticks", "task_name", "objective", "recent_auth_logs", 
                          "recent_network_logs", "recent_process_logs", "blocked_ips", 
                          "isolated_hosts", "alerts", "active_threat"]
        
        for field in required_fields:
            self.assertTrue(hasattr(obs, field), f"Missing field: {field}")


class TestGraderCompliance(unittest.TestCase):
    """Test grader implementation and scoring logic."""
    
    def test_grader_returns_evaluation_result(self):
        """Test that grader.evaluate() returns proper result."""
        grader = DeterministicGrader()
        metrics = {
            "attack_detected": True,
            "difficulty": "easy",
            "first_response_tick": 5,
            "false_positives": 0,
            "wrong_actions": 0,
            "decoy_hits": 0,
            "stage_misses": 0,
            "correct_actions": 3,
            "actions_taken": ["action1", "action2", "action3"],
        }
        
        result = grader.evaluate(metrics, success=True, max_ticks=32)
        
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "score"))
        self.assertTrue(0.0 <= result.score <= 1.0)
    
    def test_score_is_bounded(self):
        """Test that scores are always between 0 and 1."""
        grader = DeterministicGrader()
        
        test_cases = [
            {"attack_detected": False, "success": False, "metrics": {}},
            {"attack_detected": True, "success": True, "metrics": {"difficulty": "hard", "first_response_tick": 1}},
            {"attack_detected": True, "success": False, "metrics": {"difficulty": "easy", "false_positives": 10}},
        ]
        
        for case in test_cases:
            metrics = case["metrics"]
            metrics.setdefault("difficulty", "medium")
            metrics.setdefault("attack_detected", case.get("attack_detected", False))
            metrics.setdefault("first_response_tick", 10)
            metrics.setdefault("false_positives", 0)
            metrics.setdefault("wrong_actions", 0)
            metrics.setdefault("decoy_hits", 0)
            metrics.setdefault("stage_misses", 0)
            metrics.setdefault("correct_actions", 0)
            metrics.setdefault("actions_taken", [])
            
            result = grader.evaluate(metrics, success=case.get("success", False), max_ticks=32)
            self.assertTrue(0.0 <= result.score <= 1.0, 
                          f"Score out of bounds: {result.score}")


class TestDeterminism(unittest.TestCase):
    """Test determinism across runs with same seed."""
    
    def test_same_seed_produces_same_results(self):
        """Test that same seed produces identical results."""
        def run_episode(seed: int) -> dict:
            task = load_task("brute_force")
            env = SimulationEnvironment(task, seed=seed)
            agent = build_agent("baseline")
            
            obs = env.reset()
            done = False
            steps = []
            
            while not done and len(steps) < 5:
                action = agent.act(obs)
                obs, reward, done, info = env.step(action)
                steps.append({
                    "action": action.action_type,
                    "target": action.target,
                    "reward": reward.value,
                })
            
            return {
                "steps": steps,
                "final_success": info.get("success", False),
            }
        
        run1 = run_episode(42)
        run2 = run_episode(42)
        
        self.assertEqual(len(run1["steps"]), len(run2["steps"]))
        for step1, step2 in zip(run1["steps"], run2["steps"]):
            self.assertEqual(step1["action"], step2["action"])
            self.assertEqual(step1["target"], step2["target"])
            self.assertAlmostEqual(step1["reward"], step2["reward"], places=4)


class TestTaskRegistry(unittest.TestCase):
    """Test task loading and registry."""
    
    def test_all_required_tasks_available(self):
        """Test that all required tasks are available."""
        required_tasks = ["brute_force", "malware_spread", "data_exfiltration"]
        available = available_tasks()
        
        for task in required_tasks:
            self.assertIn(task, available, f"Missing required task: {task}")
    
    def test_task_loads_with_required_fields(self):
        """Test that loaded tasks have required fields."""
        required_fields = ["name", "max_ticks", "objective", "difficulty"]
        
        for task_name in ["brute_force", "malware_spread", "data_exfiltration"]:
            task = load_task(task_name)
            self.assertIsInstance(task, dict)
            for field in required_fields:
                self.assertIn(field, task, f"Task {task_name} missing field: {field}")
    
    def test_difficulty_correlation(self):
        """Test that task difficulty matches expected mapping."""
        expected_difficulty = {
            "brute_force": "easy",
            "malware_spread": "medium",
            "data_exfiltration": "hard",
        }
        
        for task_name, expected_diff in expected_difficulty.items():
            task = load_task(task_name)
            self.assertEqual(task["difficulty"], expected_diff,
                           f"Task {task_name} has unexpected difficulty")


class TestScoreBenchmarks(unittest.TestCase):
    """Test baseline scores and benchmark thresholds."""
    
    def test_baseline_achieves_minimum_score(self):
        """Test that baseline agent achieves at least minimum score."""
        from scripts.run_simulation import run
        
        result = run(
            task_name="brute_force",
            agent_name="baseline",
            seed=42,
            max_steps=None,
            show_logs=False,
        )
        
        # Baseline should score at least 0.3 on easy task
        self.assertGreaterEqual(result["score"], 0.3,
                              f"Baseline score too low on easy task: {result['score']}")
    
    def test_all_difficulties_runnable(self):
        """Test that all difficulty levels can be executed."""
        from scripts.run_simulation import run
        
        difficulties = {
            "brute_force": "easy",
            "malware_spread": "medium",
            "data_exfiltration": "hard",
        }
        
        for task_name, difficulty in difficulties.items():
            try:
                result = run(
                    task_name=task_name,
                    agent_name="baseline",
                    seed=42,
                    max_steps=None,
                    show_logs=False,
                )
                
                self.assertIn("score", result)
                self.assertTrue(0.0 <= result["score"] <= 1.0)
                print(f"✓ {difficulty.upper():8} ({task_name:20}): score = {result['score']:.4f}")
                
            except Exception as e:
                self.fail(f"Failed to run {task_name}: {e}")


class TestSubmissionIntegrity(unittest.TestCase):
    """Test overall submission integrity and requirements."""
    
    def test_required_files_exist(self):
        """Test that all required files exist."""
        required_files = [
            Path("run_simulation.py"),
            Path("inference.py"),
            Path("cybersim/__init__.py"),
            Path("cybersim/models.py"),
            Path("cybersim/agents/base.py"),
            Path("cybersim/agents/baseline.py"),
            Path("cybersim/environment/core.py"),
            Path("cybersim/grader/spec.py"),
            Path("cybersim/grader/core.py"),
            Path("cybersim/tasks/registry.py"),
            Path("configs/tasks/brute_force.json"),
            Path("configs/tasks/malware_spread.json"),
            Path("configs/tasks/data_exfiltration.json"),
        ]
        
        for file_path in required_files:
            self.assertTrue(file_path.exists(), f"Missing required file: {file_path}")
    
    def test_run_simulation_is_executable(self):
        """Test that run_simulation.py can be imported and executed."""
        try:
            from scripts.run_simulation import run, main
            self.assertTrue(callable(run))
            self.assertTrue(callable(main))
        except ImportError as e:
            self.fail(f"Cannot import run_simulation: {e}")


def run_all_tests(verbosity: int = 2) -> None:
    """Run all test suites with formatted output."""
    print("\n" + "="*80)
    print("CYBERSIM AI SUBMISSION TEST SUITE")
    print("="*80 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCompliance))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentCompliance))
    suite.addTests(loader.loadTestsFromTestCase(TestGraderCompliance))
    suite.addTests(loader.loadTestsFromTestCase(TestDeterminism))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestScoreBenchmarks))
    suite.addTests(loader.loadTestsFromTestCase(TestSubmissionIntegrity))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests Run:    {result.testsRun}")
    print(f"Successes:    {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:     {len(result.failures)}")
    print(f"Errors:       {len(result.errors)}")
    print("="*80 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests(verbosity=2)
    sys.exit(0 if success else 1)

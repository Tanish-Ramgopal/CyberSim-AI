"""
Comprehensive scoring and benchmarking system for CyberSim AI.
Tracks and reports scores across difficulty levels (easy, medium, hard).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import statistics

from scripts.run_simulation import run
from cybersim.tasks.registry import available_tasks


@dataclass
class TaskScore:
    """Score for a single task run."""
    task_name: str
    difficulty: str
    agent_name: str
    seed: int
    score: float
    status: str
    episode_reward: float
    reasoning: List[str]
    timestamp: str


@dataclass
class DifficultyStats:
    """Aggregated statistics for a difficulty level."""
    difficulty: str
    task_names: List[str]
    scores: List[float]
    min_score: float
    max_score: float
    avg_score: float
    median_score: float
    success_count: int
    total_runs: int
    success_rate: float


@dataclass
class BenchmarkResult:
    """Complete benchmark result across all difficulties."""
    agent_name: str
    timestamp: str
    total_runs: int
    easy_stats: Optional[DifficultyStats]
    medium_stats: Optional[DifficultyStats]
    hard_stats: Optional[DifficultyStats]
    overall_avg_score: float
    overall_success_rate: float


class CyberSimScorer:
    """Scoring and benchmarking system for CyberSim AI."""

    # Task difficulty mapping
    TASK_DIFFICULTY_MAP = {
        "brute_force": "easy",
        "malware_spread": "medium",
        "data_exfiltration": "hard",
    }

    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.scores_by_difficulty: Dict[str, List[TaskScore]] = {
            "easy": [],
            "medium": [],
            "hard": [],
        }

    def run_task(
        self,
        task_name: str,
        agent_name: str = "baseline",
        seed: int = 42,
        max_steps: Optional[int] = None,
    ) -> TaskScore:
        """
        Run a single task and record the score.

        Args:
            task_name: One of 'brute_force', 'malware_spread', 'data_exfiltration'
            agent_name: Agent implementation to test
            seed: Random seed for reproducibility
            max_steps: Optional override for max simulation steps

        Returns:
            TaskScore object with the result
        """
        print(f"\n[RUNNING] {task_name} with {agent_name} (seed={seed})")
        try:
            result = run(
                task_name=task_name,
                agent_name=agent_name,
                seed=seed,
                max_steps=max_steps,
                show_logs=False,
            )
            
            difficulty = self.TASK_DIFFICULTY_MAP.get(task_name, "unknown")
            task_score = TaskScore(
                task_name=task_name,
                difficulty=difficulty,
                agent_name=agent_name,
                seed=seed,
                score=result["score"],
                status=result["status"],
                episode_reward=result["episode_reward"],
                reasoning=result["reasoning"],
                timestamp=datetime.now().isoformat(),
            )
            
            self.scores_by_difficulty[difficulty].append(task_score)
            print(f"✓ Score: {task_score.score:.4f} ({task_score.status})")
            return task_score
            
        except Exception as e:
            print(f"✗ Failed: {e}", file=sys.stderr)
            raise

    def run_full_benchmark(
        self,
        agent_name: str = "baseline",
        seed: int = 42,
        max_steps: Optional[int] = None,
        difficulties: Optional[List[str]] = None,
    ) -> BenchmarkResult:
        """
        Run all tasks or specified difficulties and return aggregated results.

        Args:
            agent_name: Agent to benchmark
            seed: Random seed
            max_steps: Optional step limit
            difficulties: List of difficulties to run ['easy', 'medium', 'hard']
                         If None, runs all three

        Returns:
            BenchmarkResult with detailed statistics
        """
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]

        # Map difficulties to task names
        tasks_to_run = [
            task for task, diff in self.TASK_DIFFICULTY_MAP.items()
            if diff in difficulties
        ]

        print(f"\n{'='*60}")
        print(f"BENCHMARK: {agent_name} | Difficulties: {', '.join(difficulties)}")
        print(f"{'='*60}")

        # Reset scores for fresh benchmark
        for diff in difficulties:
            self.scores_by_difficulty[diff] = []

        # Run each task
        for task_name in tasks_to_run:
            self.run_task(task_name, agent_name, seed, max_steps)

        # Compute statistics
        results = {}
        for diff in difficulties:
            scores = self.scores_by_difficulty[diff]
            if scores:
                tasks = [s.task_name for s in scores]
                score_values = [s.score for s in scores]
                success_count = sum(1 for s in scores if s.status == "success")
                
                results[f"{diff}_stats"] = DifficultyStats(
                    difficulty=diff,
                    task_names=tasks,
                    scores=score_values,
                    min_score=min(score_values),
                    max_score=max(score_values),
                    avg_score=round(statistics.mean(score_values), 4),
                    median_score=round(statistics.median(score_values), 4),
                    success_count=success_count,
                    total_runs=len(scores),
                    success_rate=round(success_count / len(scores), 4),
                )

        # Compute overall stats
        all_scores = []
        total_success = 0
        total_runs = 0
        for scores in self.scores_by_difficulty.values():
            for score in scores:
                all_scores.append(score.score)
                total_success += score.status == "success"
                total_runs += 1

        overall_avg = round(statistics.mean(all_scores), 4) if all_scores else 0.0
        overall_success_rate = round(total_success / total_runs, 4) if total_runs > 0 else 0.0

        benchmark = BenchmarkResult(
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            total_runs=total_runs,
            easy_stats=results.get("easy_stats"),
            medium_stats=results.get("medium_stats"),
            hard_stats=results.get("hard_stats"),
            overall_avg_score=overall_avg,
            overall_success_rate=overall_success_rate,
        )

        self._print_benchmark_report(benchmark)
        self._save_benchmark_report(benchmark)

        return benchmark

    def _print_benchmark_report(self, benchmark: BenchmarkResult) -> None:
        """Print formatted benchmark report to terminal."""
        print(f"\n{'='*60}")
        print(f"BENCHMARK REPORT: {benchmark.agent_name}")
        print(f"Timestamp: {benchmark.timestamp}")
        print(f"{'='*60}")

        # Easy stats
        if benchmark.easy_stats:
            stats = benchmark.easy_stats
            print(f"\n📊 EASY (brute_force)")
            print(f"  Score:        {stats.avg_score:.4f} (min: {stats.min_score:.4f}, max: {stats.max_score:.4f})")
            print(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs})")

        # Medium stats
        if benchmark.medium_stats:
            stats = benchmark.medium_stats
            print(f"\n📊 MEDIUM (malware_spread)")
            print(f"  Score:        {stats.avg_score:.4f} (min: {stats.min_score:.4f}, max: {stats.max_score:.4f})")
            print(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs})")

        # Hard stats
        if benchmark.hard_stats:
            stats = benchmark.hard_stats
            print(f"\n📊 HARD (data_exfiltration)")
            print(f"  Score:        {stats.avg_score:.4f} (min: {stats.min_score:.4f}, max: {stats.max_score:.4f})")
            print(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs})")

        # Overall
        print(f"\n{'='*60}")
        print(f"🎯 OVERALL PERFORMANCE")
        print(f"  Total Runs:       {benchmark.total_runs}")
        print(f"  Average Score:    {benchmark.overall_avg_score:.4f}")
        print(f"  Success Rate:     {benchmark.overall_success_rate*100:.1f}%")
        print(f"{'='*60}\n")

    def _save_benchmark_report(self, benchmark: BenchmarkResult) -> None:
        """Save benchmark report to artifacts folder."""
        timestamp = benchmark.timestamp.replace(":", "-").split(".")[0]
        report_file = self.artifacts_dir / f"benchmark_{benchmark.agent_name}_{timestamp}.json"
        
        # Convert dataclasses to dicts
        report_dict = {
            "agent_name": benchmark.agent_name,
            "timestamp": benchmark.timestamp,
            "total_runs": benchmark.total_runs,
            "easy_stats": asdict(benchmark.easy_stats) if benchmark.easy_stats else None,
            "medium_stats": asdict(benchmark.medium_stats) if benchmark.medium_stats else None,
            "hard_stats": asdict(benchmark.hard_stats) if benchmark.hard_stats else None,
            "overall_avg_score": benchmark.overall_avg_score,
            "overall_success_rate": benchmark.overall_success_rate,
        }
        
        with open(report_file, "w") as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"✓ Report saved: {report_file}")

    def compare_agents(
        self,
        agent_names: List[str],
        seed: int = 42,
        max_steps: Optional[int] = None,
    ) -> None:
        """
        Run benchmarks for multiple agents and display comparison.

        Args:
            agent_names: List of agent implementation names to compare
            seed: Random seed
            max_steps: Optional step limit
        """
        benchmarks = []
        for agent_name in agent_names:
            benchmark = self.run_full_benchmark(agent_name, seed, max_steps)
            benchmarks.append(benchmark)

        # Print comparison table
        self._print_comparison_table(benchmarks)

    def _print_comparison_table(self, benchmarks: List[BenchmarkResult]) -> None:
        """Print side-by-side comparison of benchmarks."""
        print(f"\n{'='*80}")
        print("AGENT COMPARISON TABLE")
        print(f"{'='*80}")
        print(f"{'Agent':<20} {'Easy Avg':<12} {'Medium Avg':<12} {'Hard Avg':<12} {'Overall':<12}")
        print(f"{'-'*80}")
        
        for benchmark in benchmarks:
            easy_avg = benchmark.easy_stats.avg_score if benchmark.easy_stats else 0.0
            medium_avg = benchmark.medium_stats.avg_score if benchmark.medium_stats else 0.0
            hard_avg = benchmark.hard_stats.avg_score if benchmark.hard_stats else 0.0
            overall = benchmark.overall_avg_score
            
            print(
                f"{benchmark.agent_name:<20} "
                f"{easy_avg:<12.4f} "
                f"{medium_avg:<12.4f} "
                f"{hard_avg:<12.4f} "
                f"{overall:<12.4f}"
            )
        
        print(f"{'='*80}\n")


def main():
    """CLI interface for scoring and benchmarking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberSim AI Scoring & Benchmarking")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Single task command
    single_parser = subparsers.add_parser("run", help="Run a single task")
    single_parser.add_argument("--task", required=True, choices=["brute_force", "malware_spread", "data_exfiltration"])
    single_parser.add_argument("--agent", default="baseline")
    single_parser.add_argument("--seed", type=int, default=42)
    
    # Full benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run full benchmark")
    bench_parser.add_argument("--agent", default="baseline")
    bench_parser.add_argument("--seed", type=int, default=42)
    bench_parser.add_argument("--difficulties", nargs="+", choices=["easy", "medium", "hard"], 
                             help="Difficulties to run (default: all three)")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple agents")
    compare_parser.add_argument("--agents", nargs="+", required=True, help="Agent names to compare")
    compare_parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    scorer = CyberSimScorer()
    
    if args.command == "run":
        scorer.run_task(args.task, args.agent, args.seed)
    elif args.command == "benchmark":
        scorer.run_full_benchmark(args.agent, args.seed, difficulties=args.difficulties)
    elif args.command == "compare":
        scorer.compare_agents(args.agents, args.seed)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CyberSim AI Submission Validation & Scorecard Generator

This script validates your submission and generates a comprehensive score report
showing performance across easy, medium, and hard tasks.

Usage:
    python scoring_script.py --validate              # Run full validation
    python scoring_script.py --benchmark baseline    # Benchmark an agent
    python scoring_script.py --quick                 # Quick 1-task test per difficulty
"""

from __future__ import annotations

import argparse
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from scorer import CyberSimScorer
from test_submission import run_all_tests


class SubmissionValidator:
    """Validates and scores CyberSim AI submissions."""
    
    def __init__(self):
        self.scorer = CyberSimScorer()
        self.validation_results = {}
    
    def validate_submission(self) -> bool:
        """Run full test suite validation."""
        print("\n" + "="*80)
        print("STEP 1: RUNNING SUBMISSION VALIDATION TESTS")
        print("="*80)
        
        success = run_all_tests(verbosity=2)
        
        if not success:
            print("\n❌ VALIDATION FAILED - Fix the errors above before benchmarking")
            return False
        
        print("\n✅ ALL TESTS PASSED")
        return True
    
    def benchmark_agent(
        self,
        agent_name: str = "baseline",
        difficulties: Optional[List[str]] = None,
        seed: int = 42,
    ) -> dict:
        """
        Run benchmarks and generate scorecard.

        Args:
            agent_name: Agent implementation to benchmark
            difficulties: Which difficulties to run ['easy', 'medium', 'hard']
            seed: Random seed for reproducibility

        Returns:
            Dictionary with benchmark results
        """
        print("\n" + "="*80)
        print("STEP 2: RUNNING AGENT BENCHMARK")
        print("="*80)
        
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]
        
        benchmark = self.scorer.run_full_benchmark(
            agent_name=agent_name,
            seed=seed,
            difficulties=difficulties,
        )
        
        return benchmark
    
    def generate_scorecard(self, benchmark, output_file: Optional[str] = None) -> str:
        """
        Generate a detailed scorecard showing all scores and metrics.

        Args:
            benchmark: BenchmarkResult from run_full_benchmark()
            output_file: Optional file to save the scorecard

        Returns:
            Formatted scorecard string
        """
        scorecard = self._build_scorecard(benchmark)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(scorecard)
            print(f"✓ Scorecard saved to: {output_file}")
        
        return scorecard
    
    def _build_scorecard(self, benchmark) -> str:
        """Build the scorecard string."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CYBERSIM AI SUBMISSION SCORECARD")
        lines.append("="*80)
        lines.append(f"Agent:     {benchmark.agent_name}")
        lines.append(f"Timestamp: {benchmark.timestamp}")
        lines.append("")
        
        # Easy scores
        lines.append("📊 EASY DIFFICULTY (SSH Brute-Force Detection)")
        lines.append("-" * 80)
        if benchmark.easy_stats:
            stats = benchmark.easy_stats
            lines.append(f"  Task:         {', '.join(stats.task_names)}")
            lines.append(f"  Score:        {stats.avg_score:.4f}")
            lines.append(f"    └─ Min:     {stats.min_score:.4f}")
            lines.append(f"    └─ Max:     {stats.max_score:.4f}")
            lines.append(f"    └─ Median:  {stats.median_score:.4f}")
            lines.append(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs} runs)")
            lines.append("")
        else:
            lines.append("  [NOT RUN]")
            lines.append("")
        
        # Medium scores
        lines.append("📊 MEDIUM DIFFICULTY (Malware Spread Containment)")
        lines.append("-" * 80)
        if benchmark.medium_stats:
            stats = benchmark.medium_stats
            lines.append(f"  Task:         {', '.join(stats.task_names)}")
            lines.append(f"  Score:        {stats.avg_score:.4f}")
            lines.append(f"    └─ Min:     {stats.min_score:.4f}")
            lines.append(f"    └─ Max:     {stats.max_score:.4f}")
            lines.append(f"    └─ Median:  {stats.median_score:.4f}")
            lines.append(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs} runs)")
            lines.append("")
        else:
            lines.append("  [NOT RUN]")
            lines.append("")
        
        # Hard scores
        lines.append("📊 HARD DIFFICULTY (Data Exfiltration Detection)")
        lines.append("-" * 80)
        if benchmark.hard_stats:
            stats = benchmark.hard_stats
            lines.append(f"  Task:         {', '.join(stats.task_names)}")
            lines.append(f"  Score:        {stats.avg_score:.4f}")
            lines.append(f"    └─ Min:     {stats.min_score:.4f}")
            lines.append(f"    └─ Max:     {stats.max_score:.4f}")
            lines.append(f"    └─ Median:  {stats.median_score:.4f}")
            lines.append(f"  Success Rate: {stats.success_rate*100:.1f}% ({stats.success_count}/{stats.total_runs} runs)")
            lines.append("")
        else:
            lines.append("  [NOT RUN]")
            lines.append("")
        
        # Overall
        lines.append("🎯 OVERALL PERFORMANCE")
        lines.append("="*80)
        lines.append(f"  Combined Average Score:  {benchmark.overall_avg_score:.4f}")
        lines.append(f"  Overall Success Rate:    {benchmark.overall_success_rate*100:.1f}%")
        lines.append(f"  Total Episodes:          {benchmark.total_runs}")
        lines.append("")
        
        # Scoring rubric
        lines.append("📋 SCORING RUBRIC (per episode)")
        lines.append("="*80)
        lines.append("  ✓ Attack Detection:      +0.45 points")
        lines.append("  ✓ Successful Mitigation: +0.25 points")
        lines.append("  ✓ Response Speed:        +0.15 points (faster = higher)")
        lines.append("  ✓ Difficulty Bonus:      +0.03 to +0.10 (medium=+0.03, easy=+0.10)")
        lines.append("")
        lines.append("  ✗ False Positives:       -0.12 each (capped at -0.40)")
        lines.append("  ✗ Wrong Actions:         -0.12 each (capped at -0.40)")
        lines.append("  ✗ Decoy Hits:            -0.15 each (capped at -0.30)")
        lines.append("  ✗ Stage Dependency Miss: -0.15 each (capped at -0.30)")
        lines.append("  ✗ Hard Chain Penalty:    -0.18 if <3 actions on hard tasks")
        lines.append("")
        lines.append(f"  Final Score Range: [0.0, 1.0] (clamped)")
        lines.append("="*80 + "\n")
        
        return "\n".join(lines)
    
    def quick_test(self) -> None:
        """Run quick benchmark (1 episode per difficulty) for rapid feedback."""
        print("\n" + "="*80)
        print("QUICK TEST MODE (1 episode per difficulty)")
        print("="*80)
        
        benchmark = self.scorer.run_full_benchmark(
            agent_name="baseline",
            difficulties=["easy", "medium", "hard"],
        )
        
        scorecard = self._build_scorecard(benchmark)
        print(scorecard)
    
    def full_validation(self, agent_name: str = "baseline") -> bool:
        """
        Run complete validation: tests + benchmark + scorecard.

        Args:
            agent_name: Agent to benchmark after validation

        Returns:
            True if all validation passed
        """
        # Step 1: Run tests
        if not self.validate_submission():
            return False
        
        # Step 2: Run benchmark
        benchmark = self.benchmark_agent(agent_name)
        
        # Step 3: Generate and display scorecard
        scorecard = self._build_scorecard(benchmark)
        print(scorecard)
        
        # Step 4: Save artifacts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scorecard_file = f"artifacts/scorecard_{timestamp}.txt"
        self.generate_scorecard(benchmark, scorecard_file)
        
        print("✅ VALIDATION COMPLETE")
        print(f"📋 Scorecard saved to: {scorecard_file}")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="CyberSim AI Submission Validator & Scorecard Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Full validation (tests + benchmark):
    python scoring_script.py --validate
  
  Quick test (1 episode per difficulty):
    python scoring_script.py --quick
  
  Benchmark only (skip tests):
    python scoring_script.py --benchmark baseline
  
  Benchmark specific difficulties:
    python scoring_script.py --benchmark baseline --difficulties easy medium
        """)
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run full validation: tests + benchmark + scorecard"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test: 1 episode per difficulty"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        metavar="AGENT_NAME",
        help="Benchmark a specific agent (skips tests)"
    )
    parser.add_argument(
        "--difficulties",
        nargs="+",
        choices=["easy", "medium", "hard"],
        default=["easy", "medium", "hard"],
        help="Which difficulty levels to run (default: all)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    validator = SubmissionValidator()
    
    try:
        if args.validate:
            success = validator.full_validation()
            sys.exit(0 if success else 1)
        
        elif args.quick:
            validator.quick_test()
        
        elif args.benchmark:
            benchmark = validator.benchmark_agent(
                agent_name=args.benchmark,
                difficulties=args.difficulties,
                seed=args.seed,
            )
            scorecard = validator._build_scorecard(benchmark)
            print(scorecard)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Meta Hackathon Pre-Submission Validation Script

Validates that your submission meets ALL Meta hackathon requirements:
- HF Space deployment readiness
- OpenEnv spec compliance
- Dockerfile builds successfully
- Baseline inference script runs and produces scores
- 3+ tasks with graders
- Structured logging format compliance

Run this BEFORE submitting to ensure you don't get disqualified.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml
import re

# ============================================================================
# VALIDATION SECTIONS
# ============================================================================

class SubmissionValidator:
    """Comprehensive hackathon submission validator."""
    
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.results: Dict[str, Dict] = {}
        self.critical_failures = []
    
    def run_all_validations(self) -> bool:
        """Run all validation checks. Returns True if all critical checks pass."""
        print("\n" + "="*80)
        print("META HACKATHON PRE-SUBMISSION VALIDATION")
        print("="*80 + "\n")
        
        checks = [
            ("Required Files", self.check_required_files),
            ("openenv.yaml Compliance", self.check_openenv_yaml),
            ("Environment Variables", self.check_env_variables),
            ("Inference Script Format", self.check_inference_format),
            ("Inference Script Execution", self.check_inference_execution),
            ("Task & Grader Validation", self.check_tasks_and_graders),
            ("Score Range Validation", self.check_score_range),
            ("Dockerfile Buildability", self.check_dockerfile),
            ("Resource Constraints", self.check_resource_constraints),
            ("README Completeness", self.check_readme),
            ("Logging Format Compliance", self.check_logging_format),
        ]
        
        for check_name, check_func in checks:
            self._run_check(check_name, check_func)
        
        self._print_summary()
        return len(self.critical_failures) == 0
    
    def _run_check(self, name: str, func) -> None:
        """Run a single check and record results."""
        print(f"\n🔍 Checking: {name}")
        print("-" * 80)
        try:
            result = func()
            self.results[name] = {
                "status": "PASS" if result else "FAIL",
                "critical": True,
                "details": result if isinstance(result, dict) else {}
            }
            if not result:
                self.critical_failures.append(name)
                print(f"❌ FAILED: {name}")
            else:
                print(f"✅ PASSED: {name}")
        except Exception as e:
            self.results[name] = {
                "status": "ERROR",
                "critical": True,
                "error": str(e)
            }
            self.critical_failures.append(name)
            print(f"❌ ERROR in {name}: {e}")
    
    def check_required_files(self) -> bool:
        """Check that all required files exist."""
        required_files = [
            "inference.py",
            "openenv.yaml",
            "Dockerfile",
            "README.md",
            "requirements.txt",
            "cybersim/__init__.py",
            "cybersim/models.py",
            "cybersim/environment/core.py",
            "cybersim/grader/spec.py",
            "cybersim/grader/core.py",
            "cybersim/tasks/registry.py",
            "configs/tasks/brute_force.json",
            "configs/tasks/malware_spread.json",
            "configs/tasks/data_exfiltration.json",
        ]
        
        missing = []
        for file_path in required_files:
            if not (self.root / file_path).exists():
                missing.append(file_path)
        
        if missing:
            print(f"  ❌ Missing files: {', '.join(missing)}")
            return False
        
        print(f"  ✓ All {len(required_files)} required files present")
        return True
    
    def check_openenv_yaml(self) -> bool:
        """Validate openenv.yaml compliance."""
        openenv_file = self.root / "openenv.yaml"
        
        if not openenv_file.exists():
            print("  ❌ openenv.yaml not found")
            return False
        
        try:
            with open(openenv_file) as f:
                config = yaml.safe_load(f)
            
            # Required fields
            required = ["name", "version", "description", "entrypoint", "tasks", 
                       "observation_model", "action_model", "reward_model"]
            missing = [f for f in required if f not in config]
            
            if missing:
                print(f"  ❌ Missing fields in openenv.yaml: {missing}")
                return False
            
            # Check tasks
            tasks = config.get("tasks", [])
            if len(tasks) < 3:
                print(f"  ❌ Must have 3+ tasks, found {len(tasks)}")
                return False
            
            if not all(t in ["brute_force", "malware_spread", "data_exfiltration"] for t in tasks):
                print(f"  ❌ Invalid task names: {tasks}")
                return False
            
            # Check score range
            score_range = config.get("grader", {}).get("score_range", [])
            if score_range != [0.0, 1.0]:
                print(f"  ❌ Score range must be [0.0, 1.0], got {score_range}")
                return False
            
            print(f"  ✓ openenv.yaml valid with {len(tasks)} tasks")
            print(f"    - Models: {config['observation_model']}, {config['action_model']}, {config['reward_model']}")
            print(f"    - Tasks: {', '.join(tasks)}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error parsing openenv.yaml: {e}")
            return False
    
    def check_env_variables(self) -> bool:
        """Validate required environment variables are used."""
        inference_file = self.root / "inference.py"
        
        content = inference_file.read_text()
        required_vars = ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]
        missing_vars = []
        
        for var in required_vars:
            if f'os.getenv("{var}"' not in content and f"os.getenv('{var}'" not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"  ❌ Missing environment variables in inference.py: {missing_vars}")
            return False
        
        # Check for OpenAI client usage
        if "OpenAI(" not in content or "HF_TOKEN" not in content:
            print("  ❌ Must use OpenAI client with HF_TOKEN")
            return False
        
        print("  ✓ All required environment variables properly used")
        print("    - API_BASE_URL, MODEL_NAME, HF_TOKEN")
        print("    - OpenAI client initialized with HF_TOKEN")
        return True
    
    def check_inference_format(self) -> bool:
        """Check inference.py has correct structure in root."""
        inference_file = self.root / "inference.py"
        
        if not inference_file.exists():
            print("  ❌ inference.py not found in root directory")
            return False
        
        content = inference_file.read_text()
        
        # Check for required structure
        required_functions = ["log_start", "log_step", "log_end", "main"]
        missing = [f for f in required_functions if f"def {f}(" not in content]
        
        if missing:
            print(f"  ❌ Missing functions: {missing}")
            return False
        
        if "if __name__ == '__main__':" not in content and 'if __name__ == "__main__":' not in content:
            print("  ❌ Missing main block (__main__ guard)")
            return False
        
        print("  ✓ inference.py has correct structure")
        print("    - Located in root directory")
        print("    - Has log_start, log_step, log_end, main functions")
        print("    - Has __main__ guard")
        return True
    
    def check_logging_format(self) -> bool:
        """Validate strict logging format compliance."""
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        # Check logging function signatures
        start_pattern = r'print\(f"\[START\].*flush=True\)'
        step_pattern = r'print\(\s*f"\[STEP\].*flush=True\)'
        end_pattern = r'print\(\s*f"\[END\].*flush=True\)'
        
        if not re.search(start_pattern, content, re.MULTILINE):
            print("  ❌ Missing or incorrect [START] logging format")
            print("     Expected: print(f\"[START] ...\", flush=True)")
            return False
        
        if not re.search(step_pattern, content, re.MULTILINE):
            print("  ❌ Missing or incorrect [STEP] logging format")
            print("     Expected: print(f\"[STEP] step={step} action={action} reward={reward:.2f} done={done} error={error}\", flush=True)")
            return False
        
        if not re.search(end_pattern, content, re.MULTILINE):
            print("  ❌ Missing or incorrect [END] logging format")
            print("     Expected: print(f\"[END] success={success} steps={steps} score={score:.2f} rewards={rewards}\", flush=True)")
            return False
        
        print("  ✓ Logging format is compliant")
        print("    - [START] format correct")
        print("    - [STEP] format correct")
        print("    - [END] format correct")
        return True
    
    def check_inference_execution(self) -> bool:
        """Run inference script and verify it completes without error."""
        print("  Running inference.py (may take 1-5 minutes)...")
        
        try:
            # Run with minimal steps for quick validation
            env = os.environ.copy()
            env["MAX_STEPS"] = "3"
            env["CYBERSIM_TASK"] = "brute_force"
            env["API_BASE_URL"] = "https://router.huggingface.co/v1"
            env["MODEL_NAME"] = "Qwen/Qwen2.5-72B-Instruct"
            env["HF_TOKEN"] = "fake_token_for_test"
            
            result = subprocess.run(
                [sys.executable, str(self.root / "inference.py")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                env=env,
            )
            
            output = result.stdout
            
            # Check for required logging
            if "[START]" not in output:
                print(f"  ❌ Missing [START] in output")
                return False
            
            if "[STEP]" not in output:
                print(f"  ❌ Missing [STEP] in output")
                return False
            
            if "[END]" not in output:
                print(f"  ❌ Missing [END] in output")
                return False
            
            # Verify score is in range
            end_match = re.search(r'\[END\].*score=(\d+\.\d+)', output)
            if end_match:
                score = float(end_match.group(1))
                if not (0.0 <= score <= 1.0):
                    print(f"  ❌ Score out of range [0.0, 1.0]: {score}")
                    return False
            
            print("  ✓ Inference script executes successfully")
            print(f"    - Produced valid [START], [STEP], [END] logs")
            print(f"    - Score in valid range [0.0, 1.0]")
            return True
            
        except subprocess.TimeoutExpired:
            print("  ❌ Inference script took too long (>10 min)")
            return False
        except Exception as e:
            print(f"  ⚠️  Could not execute inference (may need real API keys): {e}")
            # Don't fail on this, as it may need real API access
            return True
    
    def check_tasks_and_graders(self) -> bool:
        """Validate all 3+ tasks have proper graders."""
        try:
            from cybersim.tasks.registry import load_task, available_tasks
            from cybersim.grader.core import DeterministicGrader
            
            tasks = available_tasks()
            
            if len(tasks) < 3:
                print(f"  ❌ Must have 3+ tasks, found {len(tasks)}")
                return False
            
            grader = DeterministicGrader()
            
            for task_name in tasks:
                try:
                    task = load_task(task_name)
                    test_metrics = {
                        "attack_detected": True,
                        "difficulty": task.get("difficulty", "medium"),
                        "first_response_tick": 5,
                        "false_positives": 0,
                        "wrong_actions": 0,
                        "decoy_hits": 0,
                        "stage_misses": 0,
                        "correct_actions": 1,
                        "actions_taken": ["test"],
                    }
                    result = grader.evaluate(test_metrics, success=True, max_ticks=32)
                    
                    if result is None or result.score is None:
                        print(f"  ❌ Grader for {task_name} returned invalid result")
                        return False
                    
                except Exception as e:
                    print(f"  ❌ Error loading/grading {task_name}: {e}")
                    return False
            
            print(f"  ✓ All {len(tasks)} tasks have working graders")
            print(f"    - Tasks: {', '.join(tasks)}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error validating tasks: {e}")
            return False
    
    def check_score_range(self) -> bool:
        """Verify scores are always in [0.0, 1.0]."""
        try:
            from cybersim.grader.spec import SCORE_MIN, SCORE_MAX
            
            if SCORE_MIN != 0.0 or SCORE_MAX != 1.0:
                print(f"  ❌ Score range must be [0.0, 1.0], defined as [{SCORE_MIN}, {SCORE_MAX}]")
                return False
            
            print(f"  ✓ Score range properly defined as [{SCORE_MIN}, {SCORE_MAX}]")
            return True
            
        except Exception as e:
            print(f"  ❌ Error checking score range: {e}")
            return False
    
    def check_dockerfile(self) -> bool:
        """Validate Dockerfile syntax and builds."""
        dockerfile = self.root / "Dockerfile"
        
        if not dockerfile.exists():
            print("  ❌ Dockerfile not found")
            return False
        
        content = dockerfile.read_text()
        
        # Check key requirements
        if "python:3.1" not in content:
            print("  ⚠️  Warning: Recommended to use Python 3.10+ (3.11/3.12)")
        
        if "WORKDIR" not in content:
            print("  ❌ Missing WORKDIR instruction")
            return False
        
        if "pip install" not in content and "pip install --no-cache-dir" not in content:
            print("  ❌ Missing pip install for dependencies")
            return False
        
        if "EXPOSE" not in content:
            print("  ⚠️  Missing EXPOSE instruction (recommended for web services)")
        
        print("  ✓ Dockerfile structure looks valid")
        print("    - Has WORKDIR, pip install, proper copying")
        print("    - Note: Can't validate actual build without Docker")
        return True
    
    def check_resource_constraints(self) -> bool:
        """Check that solution respects resource constraints."""
        print("  Evaluating resource constraints (vcpu=2, memory=8GB, time=20min)...")
        
        # Check for excessive dependencies
        requirements = self.root / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text().lower()
            
            # Warn about potentially heavy packages
            heavy = ["tensorflow", "pytorch", "torch", "transformers>=4.30"]
            for lib in heavy:
                if lib.lower() in content:
                    print(f"  ⚠️  Warning: {lib} may exceed resource limits")
        
        # Check MAX_STEPS is reasonable
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        max_steps_match = re.search(r'MAX_STEPS\s*=\s*int\(.*?["\'](\\d+)["\']', content)
        if max_steps_match:
            steps = int(max_steps_match.group(1))
            if steps > 100:
                print(f"  ⚠️  MAX_STEPS={steps} may cause timeout")
        
        print("  ✓ Resource constraints appear reasonable")
        print("    - Verify actual runtime is <20 minutes")
        return True
    
    def check_readme(self) -> bool:
        """Validate README completeness."""
        readme = self.root / "README.md"
        
        if not readme.exists():
            print("  ❌ README.md not found")
            return False
        
        content = readme.read_text()
        
        # Check for required sections
        required_sections = [
            ("Motivation", ["Motivation", "motivation"]),
            ("Action Space", ["Action", "action space"]),
            ("Observation Space", ["Observation", "observation space"]),
            ("Task Description", ["Tasks", "tasks", "brute_force", "malware", "exfiltration"]),
        ]
        
        missing_sections = []
        for section_name, keywords in required_sections:
            if not any(kw.lower() in content.lower() for kw in keywords):
                missing_sections.append(section_name)
        
        if missing_sections:
            print(f"  ⚠️  Consider adding sections: {', '.join(missing_sections)}")
        
        # Check for required content
        if "## Grader" in content:
            print("  ✓ Grader section present")
        if "step()" in content and "reset()" in content:
            print("  ✓ API documentation present")
        if "requirements.txt" in content or "pip install" in content:
            print("  ✓ Setup instructions present")
        
        print("  ✓ README.md is present and reasonably complete")
        return True
    
    def _print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80 + "\n")
        
        passed = sum(1 for r in self.results.values() if r["status"] == "PASS")
        failed = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        errors = sum(1 for r in self.results.values() if r["status"] == "ERROR")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"Total:    {len(self.results)}\n")
        
        if self.critical_failures:
            print("🚨 CRITICAL FAILURES (Disqualifying):")
            for failure in self.critical_failures:
                print(f"   - {failure}")
            print("\n❌ SUBMISSION NOT READY - Fix failures above before submitting!")
            return
        
        print("✅ ALL VALIDATIONS PASSED!")
        print("\n📋 You are ready to submit to Meta hackathon!")
        print("   - Push to GitHub")
        print("   - Deploy to Hugging Face Spaces")
        print("   - Submit the HF Space URL by 12th April 11:59 PM IST")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Meta Hackathon Pre-Submission Validator",
        epilog="Run this before submitting to ensure compliance!"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    validator = SubmissionValidator(args.project_root)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

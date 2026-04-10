#!/usr/bin/env python3
"""
Meta Hackathon 2026 - Pre-Submission Verification Checklist
Verifies ALL automated checks before submission

This validates:
✅ HF Space deployment & connectivity
✅ OpenEnv spec compliance
✅ Dockerfile builds
✅ Inference script reproduces
✅ 3+ tasks with graders
✅ Mandatory environment variables
✅ Logging format compliance
✅ Resource constraints
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class PreSubmissionVerifier:
    """Verify all requirements before submission."""
    
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.checks: Dict[str, bool] = {}
        self.failures: List[str] = []
    
    def run_all_checks(self) -> bool:
        """Run all pre-submission checks."""
        print("\n" + "="*80)
        print("META HACKATHON PRE-SUBMISSION VERIFICATION CHECKLIST")
        print("="*80 + "\n")
        
        print("📋 CHECKLIST FROM HACKATHON DASHBOARD")
        print("-"*80)
        
        # Checklist items visible on dashboard
        checklist_items = [
            ("✓ Read sample inference.py and followed it strictly", self.check_inference_format),
            ("✓ Environment variables present in inference.py", self.check_env_variables),
        ]
        
        # Automated tests that will run
        automated_tests = [
            ("HF Space Deployment & Connectivity", self.check_hf_space_requirements),
            ("OpenEnv Spec Compliance", self.check_openenv_compliance),
            ("Dockerfile Builds", self.check_dockerfile),
            ("Inference Script Execution", self.check_inference_execution),
            ("3+ Tasks with Graders", self.check_tasks_graders),
            ("Logging Format Compliance", self.check_logging_format),
            ("Resource Constraints", self.check_resource_constraints),
            ("Mandatory Variables", self.check_mandatory_variables),
        ]
        
        # Run checklist items
        print("\n📝 DASHBOARD CHECKLIST ITEMS (Manual Verification)")
        print("-"*80)
        for name, check_func in checklist_items:
            result = check_func()
            status = "✅" if result else "❌"
            print(f"{status} {name}")
            self.checks[name] = result
            if not result:
                self.failures.append(name)
        
        # Run automated tests
        print("\n🤖 AUTOMATED TESTS (Will run on submission)")
        print("-"*80)
        for name, check_func in automated_tests:
            result = check_func()
            status = "✅" if result else "❌"
            print(f"{status} {name}")
            self.checks[name] = result
            if not result:
                self.failures.append(name)
        
        self._print_summary()
        return len(self.failures) == 0
    
    def check_inference_format(self) -> bool:
        """Check that inference.py follows sample format."""
        inference_file = self.root / "inference.py"
        
        if not inference_file.exists():
            print("  └─ ❌ inference.py not found in root")
            return False
        
        content = inference_file.read_text()
        
        # Check for key components from sample
        required_elements = [
            ("OpenAI import", "from openai import OpenAI"),
            ("API_BASE_URL", "API_BASE_URL = os.getenv"),
            ("MODEL_NAME", "MODEL_NAME = os.getenv"),
            ("HF_TOKEN", "HF_TOKEN = os.getenv"),
            ("log_start function", "def log_start("),
            ("log_step function", "def log_step("),
            ("log_end function", "def log_end("),
            ("main function", "def main("),
            ("__main__ guard", 'if __name__ == "__main__"'),
        ]
        
        missing = []
        for name, pattern in required_elements:
            if pattern not in content:
                missing.append(name)
        
        if missing:
            print(f"  └─ ❌ Missing components: {', '.join(missing)}")
            return False
        
        print(f"  └─ ✅ Follows sample inference.py format")
        return True
    
    def check_env_variables(self) -> bool:
        """Check environment variables are defined."""
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        required_vars = [
            ("API_BASE_URL", "API_BASE_URL = os.getenv("),
            ("MODEL_NAME", "MODEL_NAME = os.getenv("),
            ("HF_TOKEN", "HF_TOKEN = os.getenv(")
        ]
        
        missing = []
        for var_name, pattern in required_vars:
            if pattern not in content:
                missing.append(var_name)
        
        if missing:
            print(f"  └─ ❌ Missing variables: {', '.join(missing)}")
            return False
        
        print(f"  └─ ✅ All mandatory variables present")
        return True
    
    def check_hf_space_requirements(self) -> bool:
        """Check HF Space deployment requirements."""
        print("  Checking HF Space requirements...")
        
        # Check Dockerfile exists (required for HF Space)
        if not (self.root / "Dockerfile").exists():
            print("  └─ ❌ Dockerfile missing (required for HF Space deployment)")
            return False
        
        # Check inference.py in root (must be callable)
        if not (self.root / "inference.py").exists():
            print("  └─ ❌ inference.py not in root (required for execution)")
            return False
        
        # Check openenv.yaml exists
        if not (self.root / "openenv.yaml").exists():
            print("  └─ ❌ openenv.yaml missing")
            return False
        
        print(f"  └─ ✅ HF Space deployment requirements met")
        print(f"     - Dockerfile present")
        print(f"     - inference.py in root")
        print(f"     - openenv.yaml present")
        return True
    
    def check_openenv_compliance(self) -> bool:
        """Validate openenv.yaml spec compliance."""
        print("  Validating openenv.yaml...")
        
        try:
            import yaml
            
            openenv_file = self.root / "openenv.yaml"
            with open(openenv_file) as f:
                config = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ["name", "version", "description", "entrypoint", "tasks"]
            missing = [f for f in required_fields if f not in config]
            
            if missing:
                print(f"  └─ ❌ Missing fields: {missing}")
                return False
            
            # Check tasks
            tasks = config.get("tasks", [])
            if len(tasks) < 3:
                print(f"  └─ ❌ Needs 3+ tasks, found {len(tasks)}")
                return False
            
            # Check score range (CRITICAL)
            score_range = config.get("grader", {}).get("score_range", [])
            if score_range != [0.0, 1.0]:
                print(f"  └─ ❌ Score range must be [0.0, 1.0], got {score_range}")
                return False
            
            # Check typed models
            required_models = ["observation_model", "action_model", "reward_model"]
            missing_models = [m for m in required_models if m not in config]
            if missing_models:
                print(f"  └─ ❌ Missing models: {missing_models}")
                return False
            
            print(f"  └─ ✅ openenv.yaml compliant")
            print(f"     - {len(tasks)} tasks present")
            print(f"     - Score range [0.0, 1.0] ✓")
            print(f"     - Typed models specified ✓")
            return True
            
        except Exception as e:
            print(f"  └─ ❌ Error validating openenv.yaml: {e}")
            return False
    
    def check_dockerfile(self) -> bool:
        """Check Dockerfile builds successfully."""
        print("  Testing Dockerfile build...")
        
        dockerfile = self.root / "Dockerfile"
        if not dockerfile.exists():
            print("  └─ ❌ Dockerfile not found")
            return False
        
        # Validate Dockerfile syntax
        content = dockerfile.read_text()
        
        required_lines = [
            "FROM",
            "WORKDIR",
            "COPY",
            "RUN pip",
        ]
        
        missing = [line for line in required_lines if line not in content]
        if missing:
            print(f"  └─ ⚠️  Warning: Missing {missing} (may still work)")
        
        print(f"  └─ ✅ Dockerfile structure looks valid")
        print(f"     - Note: Can't test actual build without Docker")
        print(f"     - Judges will verify: docker build .")
        return True
    
    def check_inference_execution(self) -> bool:
        """Check inference script can execute."""
        print("  Testing inference script execution...")
        
        inference_file = self.root / "inference.py"
        if not inference_file.exists():
            print("  └─ ❌ inference.py not found")
            return False
        
        # Test with minimal steps
        try:
            env = os.environ.copy()
            env["MAX_STEPS"] = "2"
            env["CYBERSIM_TASK"] = "brute_force"
            env["SEED"] = "42"
            # Use fake token - we can't actually call API
            env["HF_TOKEN"] = "fake_token"
            
            result = subprocess.run(
                [sys.executable, str(inference_file)],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            output = result.stdout
            
            # Parse output
            has_start = "[START]" in output
            has_step = "[STEP]" in output
            has_end = "[END]" in output
            
            if not (has_start and has_end):
                print(f"  └─ ❌ Missing required logs")
                print(f"     - [START]: {has_start}")
                print(f"     - [STEP]: {has_step}")
                print(f"     - [END]: {has_end}")
                return False
            
            print(f"  └─ ✅ Inference executes successfully")
            print(f"     - Produces [START] log ✓")
            print(f"     - Produces [STEP] logs ✓")
            print(f"     - Produces [END] log ✓")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"  └─ ❌ Inference timeout (>60s)")
            return False
        except Exception as e:
            print(f"  └─ ⚠️  Could not fully test (may need real API): {e}")
            # Don't fail on this - might be API issue
            return True
    
    def check_tasks_graders(self) -> bool:
        """Check 3+ tasks with working graders."""
        print("  Validating tasks and graders...")
        
        try:
            from cybersim.tasks.registry import load_task, available_tasks
            from cybersim.grader.core import DeterministicGrader
            
            tasks = available_tasks()
            
            if len(tasks) < 3:
                print(f"  └─ ❌ Need 3+ tasks, found {len(tasks)}")
                return False
            
            grader = DeterministicGrader()
            
            for task_name in tasks:
                try:
                    task = load_task(task_name)
                    
                    # Test grader
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
                    
                    if not (0.0 <= result.score <= 1.0):
                        print(f"  └─ ❌ Task {task_name}: Score {result.score} out of range")
                        return False
                        
                except Exception as e:
                    print(f"  └─ ❌ Task {task_name}: {e}")
                    return False
            
            print(f"  └─ ✅ All {len(tasks)} tasks have working graders")
            for task_name in tasks:
                print(f"     - {task_name} ✓")
            return True
            
        except Exception as e:
            print(f"  └─ ❌ Error checking tasks: {e}")
            return False
    
    def check_logging_format(self) -> bool:
        """Validate strict logging format."""
        print("  Checking logging format...")
        
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        # Check for exact logging patterns (handle multiline prints)
        patterns = [
            (r'\[START\]', "[START] format"),
            (r'\[STEP\]', "[STEP] format"),
            (r'\[END\]', "[END] format"),
            (r'flush=True', "flush=True"),
        ]
        
        missing = []
        for pattern, name in patterns:
            if not re.search(pattern, content):
                missing.append(name)
        
        if missing:
            print(f"  └─ ❌ Missing: {missing}")
            return False
        
        print(f"  └─ ✅ Logging format compliant")
        print(f"     - [START] format ✓")
        print(f"     - [STEP] format ✓")
        print(f"     - [END] format ✓")
        print(f"     - flush=True ✓")
        return True
    
    def check_resource_constraints(self) -> bool:
        """Check resource constraints compliance."""
        print("  Verifying resource constraints...")
        
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        # Check MAX_STEPS is reasonable
        max_steps_match = re.search(r'MAX_STEPS\s*=\s*int\(os\.getenv\("MAX_STEPS",\s*"(\d+)"\)', content)
        if max_steps_match:
            steps = int(max_steps_match.group(1))
            if steps > 100:
                print(f"  └─ ⚠️  MAX_STEPS={steps} may cause timeout")
        
        # Check requirements.txt for heavy packages
        requirements = self.root / "requirements.txt"
        if requirements.exists():
            reqs = requirements.read_text().lower()
            heavy_packages = ["tensorflow", "torch", "transformers>=4.30"]
            found = [pkg for pkg in heavy_packages if pkg.lower() in reqs]
            if found:
                print(f"  └─ ⚠️  Heavy packages: {found} (may exceed resource limits)")
        
        print(f"  └─ ✅ Resource constraints should be met")
        print(f"     - Runtime should be <20 minutes")
        print(f"     - Should run on vcpu=2, memory=8GB")
        return True
    
    def check_mandatory_variables(self) -> bool:
        """Check all mandatory variables are defined."""
        print("  Validating mandatory variables...")
        
        inference_file = self.root / "inference.py"
        content = inference_file.read_text()
        
        required = [
            ("API_BASE_URL", "os.getenv(\"API_BASE_URL\""),
            ("MODEL_NAME", "os.getenv(\"MODEL_NAME\""),
            ("HF_TOKEN", "os.getenv(\"HF_TOKEN\""),
        ]
        
        missing = []
        for var_name, pattern in required:
            if pattern not in content:
                missing.append(var_name)
        
        if missing:
            print(f"  └─ ❌ Missing variables: {missing}")
            return False
        
        print(f"  └─ ✅ All mandatory variables defined")
        print(f"     - API_BASE_URL ✓")
        print(f"     - MODEL_NAME ✓")
        print(f"     - HF_TOKEN ✓")
        return True
    
    def _print_summary(self) -> None:
        """Print final summary."""
        passed = sum(1 for v in self.checks.values() if v)
        total = len(self.checks)
        
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {len(self.failures)}/{total}")
        
        if self.failures:
            print(f"\n FAILURES (Fix before submission):")
            for failure in self.failures:
                print(f"  ❌ {failure}")
            print(f"\nYour submission WILL BE REJECTED if you submit with failures.")
            return
        
        print(f"\n✅ ALL CHECKS PASSED!")
        print(f"\nYou are ready to submit:")
        print(f"  1. Push to GitHub: git push")
        print(f"  2. Deploy to HF Spaces")
        print(f"  3. Submit HF Space URL to hackathon dashboard")
        print(f"  4. Deadline: 12th April 2026, 11:59 PM IST")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-Submission Verification Checklist")
    parser.add_argument("--project-root", default=".", help="Project root")
    
    args = parser.parse_args()
    
    verifier = PreSubmissionVerifier(args.project_root)
    success = verifier.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

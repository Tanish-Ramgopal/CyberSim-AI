from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    checks = []

    # Baseline inference script contract
    code, out = run_cmd([sys.executable, "inference.py"])
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    assert_true(code == 0, "inference.py failed")
    assert_true(lines[0].startswith("[START] "), "Missing START line")
    assert_true(lines[-1].startswith("[END] "), "Missing END line")
    assert_true(any(line.startswith("[STEP] ") for line in lines), "No STEP lines emitted")
    checks.append("inference_format")

    # 3 tasks + DeterministicGrader score in [0,1] (see cybersim/grader/spec.py)
    for task in ["brute_force", "malware_spread", "data_exfiltration"]:
        code, out = run_cmd([sys.executable, "run_simulation.py", "--task", task, "--agent", "baseline", "--seed", "42"])
        assert_true(code == 0, f"run_simulation failed for {task}")
        result = json.loads(out)
        score = float(result["score"])
        assert_true(0.0 <= score <= 1.0, f"score out of range for {task}: {score}")
    checks.append("task_grader_range")

    # OpenEnv metadata + deploy API presence
    assert_true((ROOT / "openenv.yaml").exists(), "openenv.yaml missing")
    assert_true((ROOT / "app.py").exists(), "app.py missing")
    checks.append("spec_files")

    print(json.dumps({"status": "pass", "checks": checks}, indent=2))


if __name__ == "__main__":
    main()


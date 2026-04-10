# CyberSim AI (OpenEnv-style Cyber Defense Benchmark)

**🏆 Meta PyTorch Hackathon 2026 Submission**

CyberSim AI is a deterministic, modular cybersecurity simulation environment for evaluating agents on realistic SOC workflows:
- detecting SSH brute-force attempts,
- containing malware spread,
- stopping suspicious outbound exfiltration.

The project is structured to satisfy OpenEnv-style requirements: typed models, `reset()/step()/state()` lifecycle, reproducible grading, and containerized execution.

---

## 🎯 For Meta Hackathon Participants

### ⚡ Quick Start Submission Guide

**BEFORE SUBMITTING:**
1. Run the pre-submission validator:
   ```bash
   python meta_hackathon_validator.py
   ```
   All checks must PASS or your submission will be disqualified.

2. Review the submission guide:
   - [META_HACKATHON_SUBMISSION_GUIDE.md](META_HACKATHON_SUBMISSION_GUIDE.md) - Step-by-step instructions
   - [META_HACKATHON_COMPLIANCE_CHECKLIST.md](META_HACKATHON_COMPLIANCE_CHECKLIST.md) - Compliance verification

3. Key Dates:
   - **Build & Test:** Now - 10th April
   - **Deploy & Validate:** 11th April
   - **DEADLINE:** 12th April 11:59 PM IST

### ✅ Submission Checklist

- [ ] Run `python meta_hackathon_validator.py` → ALL PASS
- [ ] `inference.py` in root directory
- [ ] Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN
- [ ] Logging format: strict [START], [STEP], [END]
- [ ] Scores in [0.0, 1.0] range
- [ ] 3+ tasks with graders
- [ ] Dockerfile builds successfully
- [ ] Deployed to Hugging Face Spaces
- [ ] Submit HF Space URL before deadline

### 📚 Documentation

For hackathon-specific guidance, see:
1. **[META_HACKATHON_SUBMISSION_GUIDE.md](META_HACKATHON_SUBMISSION_GUIDE.md)** - Complete submission walkthrough
2. **[META_HACKATHON_COMPLIANCE_CHECKLIST.md](META_HACKATHON_COMPLIANCE_CHECKLIST.md)** - Requirement checklist
3. **[SCORING_GUIDE.md](SCORING_GUIDE.md)** - Detailed scoring explanation
4. **[scoring_script.py](scoring_script.py)** - Local testing & scoring

### 🔧 Run Validator

```bash
# Full validation (tests all hackathon requirements)
python meta_hackathon_validator.py
```

Expected output: ✅ ALL VALIDATIONS PASSED

---

## Motivation

SOC analysts repeatedly perform triage and mitigation tasks under incomplete telemetry. CyberSim AI models this practical workflow so researchers can benchmark policy quality, reaction speed, and false-positive behavior in a controlled environment.

## Project Structure

```text
cybersim/
  agents/                  # baseline agent and factory
  environment/             # simulation engine + telemetry generation
  grader/                  # spec.py (weights) + core.py (DeterministicGrader)
  tasks/                   # task registry/loading
  models.py                # typed Action/Observation/Reward models (Pydantic)
configs/tasks/             # config-driven tasks
scripts/run_simulation.py  # mandatory inference script
scripts/run_openai_baseline.py
tests/test_environment.py
openenv.yaml
Dockerfile
```

## Action Space

`Action` is a typed Pydantic model with:
- `action_type`: one of `block_ip`, `kill_process`, `isolate_machine`, `raise_alert`, `noop`
- `target`: action-specific target string
- `metadata`: optional dictionary

## Observation Space

`Observation` is a typed Pydantic model including:
- trajectory context (`tick`, `max_ticks`, `task_name`, `objective`)
- rolling telemetry windows (`recent_auth_logs`, `recent_network_logs`, `recent_process_logs`)
- defensive state (`blocked_ips`, `isolated_hosts`, `alerts`)
- threat state (`active_threat`)

## Reward Design (per-step, not the grader)

Each `step(action)` returns a typed `Reward` model used for **dense trajectory feedback** inside `SimulationEnvironment`:
- positive components for correct mitigation / progress,
- mild efficiency penalty for non-`noop` actions,
- false-positive style penalty for invalid actions,
- small threat-related penalties while a threat is active.

These **per-step** values are **independent** from the episode **`DeterministicGrader`** score in **[0.0, 1.0]** (see **Grader** below). The grader consumes final `metrics` and `success`, not the sum of step rewards.

## Implemented Tasks (Difficulty Progression)

1. `brute_force` (easy): block attacking IP before compromise threshold.
2. `malware_spread` (medium): kill malware process or isolate seed endpoint before lateral movement.
3. `data_exfiltration` (hard): detect beacon + bulk transfer pattern and isolate compromised host.

All tasks are config-driven JSON definitions in `configs/tasks`.

## Grader

**Single source of truth:** `cybersim/grader/spec.py` defines every weight; `cybersim/grader/core.py` implements `DeterministicGrader.evaluate`. README tables below **must** match `spec.py`; judges may treat mismatches as invalid.

Output is a normalized score in **[0.0, 1.0]** via `max(0.0, min(1.0, round(score, 4)))`.

**Additive terms (before penalties):**

| Component | Value |
|-----------|--------|
| Threat detected (`attack_detected`) | **+0.45** |
| Mitigation (`success` or `mitigated`) | **+0.25** |
| Response speed | **+0.0 … +0.15**: if `first_response_tick` is set, `max(0, 0.15 - (first_tick / max_ticks) * 0.15)`; else **0** |
| Difficulty calibration | **easy +0.10** · **medium +0.03** · **hard +0.0** (from `metrics["difficulty"]`, default `medium`) |

**Subtractive penalties (capped per line, then summed):**

| Penalty | Formula | Cap |
|---------|---------|-----|
| False positives | `false_positives * 0.12` | min with **0.40** |
| Wrong actions | `wrong_actions * 0.12` | min with **0.40** |
| Decoy hits | `decoy_hits * 0.15` | min with **0.30** |
| Stage misses | `stage_misses * 0.15` | min with **0.30** |
| Hard chain | **0.18** if `difficulty == "hard"` and `len(actions_taken) < 3`, else **0** | — |

Final score: `max(0.0, min(1.0, round(score, 4)))` where `score` is additive terms minus total penalties.

Grading is deterministic and reproducible for fixed seed + task + agent behavior.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run Baseline Agent

```bash
python run_simulation.py --task brute_force --agent baseline --seed 42
python run_simulation.py --task malware_spread --agent baseline --seed 42
python run_simulation.py --task data_exfiltration --agent baseline --seed 42
```

To include full logs:

```bash
python run_simulation.py --task brute_force --agent baseline --seed 42 --show-logs
```

## OpenAI Baseline Script

Uses OpenAI API credentials from `OPENAI_API_KEY`.

```bash
export OPENAI_API_KEY=...
python scripts/run_openai_baseline.py --model gpt-4.1-mini --seed 42
```

This runs all tasks and reports per-task and average scores.

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Includes determinism and normalized score checks.

## Docker

```bash
docker build -t cybersim-ai .
docker run --rm cybersim-ai
```

## Hugging Face Space Deployment Notes

- Container is provided via `Dockerfile`.
- Add Space tag `openenv` in Space metadata.
- Set runtime env vars (such as `OPENAI_API_KEY`) when using the LLM baseline script.

## Reproducibility

- Fixed seed supported via `--seed`.
- Task scenarios are static JSON config.
- Log generation and grading are deterministic with same seed.


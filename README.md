---
title: CyberSim AI
emoji: shield
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
---

# CyberSim AI (OpenEnv-style Cyber Defense Benchmark)

CyberSim AI is a deterministic, modular cybersecurity simulation environment for evaluating agents on realistic SOC workflows:
- detecting SSH brute-force attempts,
- containing malware spread,
- stopping suspicious outbound exfiltration.

The project is structured to satisfy OpenEnv-style requirements: typed models, `reset()/step()/state()` lifecycle, reproducible grading, and containerized execution.

## Motivation

SOC analysts repeatedly perform triage and mitigation tasks under incomplete telemetry. CyberSim AI models this practical workflow so researchers can benchmark policy quality, reaction speed, and false-positive behavior in a controlled environment.

## Project Structure

```text
cybersim/
  agents/                  # baseline agent and factory
  environment/             # simulation engine + telemetry generation
  grader/                  # deterministic 0.0-1.0 grader
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

## Reward Design

Each `step(action)` returns a typed `Reward` model:
- positive reward for correct mitigation/progress,
- mild efficiency penalty for excessive interventions,
- false-positive penalty for invalid actions,
- small persistent penalty while threat remains active.

This provides dense trajectory signal rather than pure terminal reward.

## Implemented Tasks (Difficulty Progression)

1. `brute_force` (easy): block attacking IP before compromise threshold.
2. `malware_spread` (medium): kill malware process or isolate seed endpoint before lateral movement.
3. `data_exfiltration` (hard): detect beacon + bulk transfer pattern and isolate compromised host.

All tasks are config-driven JSON definitions in `configs/tasks`.

## Grader

`DeterministicGrader` outputs normalized score in **[0.0, 1.0]**:
- +0.50 detected threat,
- +0.30 successful mitigation,
- +0.00..+0.20 response-time bonus,
- -0.00..-0.30 false-positive penalty.

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


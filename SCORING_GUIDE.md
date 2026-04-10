# CyberSim AI - Scoring & Testing Guide

## Overview

This guide explains **where scores are tracked**, **how testing works**, and **how to validate your submission**.

---

## 📊 Scoring System

### Difficulty Levels

Your submission is evaluated on **three difficulty levels**:

| Difficulty | Task | Focus Area |
|---|---|---|
| **Easy** | `brute_force` | SSH brute-force attack detection |
| **Medium** | `malware_spread` | Malware propagation containment |
| **Hard** | `data_exfiltration` | Data exfiltration detection & prevention |

### Score Calculation Per Episode

Each episode receives a **score from 0.0 to 1.0** based on:

**Positive Components (up to +0.97):**
- ✓ **Attack Detection**: +0.45 — Did your agent detect the threat?
- ✓ **Mitigation Success**: +0.25 — Did mitigation actions pass validation?
- ✓ **Response Speed**: +0.15 — How quickly did your agent respond? (0 if late, max 0.15 if fast)
- ✓ **Difficulty Bonus**: +0.10 (easy) / +0.03 (medium) / +0.0 (hard)

**Negative Components (penalties):**
- ✗ **False Positives**: -0.12 per invalid action (capped at -0.40)
- ✗ **Wrong Actions**: -0.12 per wrong action (capped at -0.40)
- ✗ **Decoy Hits**: -0.15 per decoy interaction (capped at -0.30)
- ✗ **Stage Dependencies**: -0.15 per missed stage (capped at -0.30)
- ✗ **Hard Chain Penalty**: -0.18 if fewer than 3 actions on hard tasks

**Final Score**: `max(0.0, min(1.0, sum of all components))`

---

## 🚀 Quick Start: Run Your First Scorecard

### Option 1: Full Validation (Recommended)

Runs tests + benchmark + generates scorecard:

```bash
python scoring_script.py --validate
```

**Output:**
```
✅ all tests pass
📊 Runs benchmarks for easy/medium/hard tasks
✓ Score: 0.5234 (easy)
✓ Score: 0.4891 (medium)
✓ Score: 0.3456 (hard)
📋 Saves detailed scorecard to artifacts/
```

### Option 2: Quick Test (Fast Feedback)

1 episode per difficulty (30 seconds):

```bash
python scoring_script.py --quick
```

### Option 3: Benchmark Only (Skip Tests)

If tests already passed:

```bash
python scoring_script.py --benchmark baseline
```

---

## 📋 Understanding Your Scorecard

When you run scoring, you get output like this:

```
================================================================================
CYBERSIM AI SUBMISSION SCORECARD
================================================================================
Agent:     baseline
Timestamp: 2026-04-11T14:32:45.123456

📊 EASY DIFFICULTY (SSH Brute-Force Detection)
────────────────────────────────────────────────────────────────────────────────
  Task:         brute_force
  Score:        0.5234                    ← Average score for this difficulty
    └─ Min:     0.4123                    ← Lowest run
    └─ Max:     0.6345                    ← Highest run
    └─ Median:  0.5289
  Success Rate: 100.0% (1/1 runs)         ← Episodes where goal achieved

📊 MEDIUM DIFFICULTY (Malware Spread Containment)
────────────────────────────────────────────────────────────────────────────────
  Task:         malware_spread
  Score:        0.4891
    └─ Min:     0.3456
    └─ Max:     0.6234
    └─ Median:  0.4912
  Success Rate: 50.0% (1/2 runs)

📊 HARD DIFFICULTY (Data Exfiltration Detection)
────────────────────────────────────────────────────────────────────────────────
  Task:         data_exfiltration
  Score:        0.3456
    └─ Min:     0.2123
    └─ Max:     0.4789
    └─ Median:  0.3612
  Success Rate: 0.0% (0/1 runs)

🎯 OVERALL PERFORMANCE
================================================================================
  Combined Average Score:  0.4527         ← Overall performance metric
  Overall Success Rate:    50.0%
  Total Episodes:          3
```

### How to Read It:

1. **Score (0.0-1.0)**: Higher is better. 0.5+ is good, 0.7+ is very good
2. **Min/Max**: Shows score variance across runs
3. **Success Rate %**: Percentage of runs where goal was achieved
4. **Difficulty Progression**: Easy score > Medium > Hard is expected

---

## 🧪 Testing Your Implementation

### Run All Tests

```bash
python -m unittest test_submission.py -v
```

Tests cover:
- ✓ Agent compliance (implements required interface)
- ✓ Environment compliance (reset/step/state lifecycle)
- ✓ Grader compliance (scoring logic)
- ✓ Determinism (same seed = same results)
- ✓ Task registry (all tasks loadable)
- ✓ Score bounds (scores 0.0-1.0)
- ✓ Submission integrity (all files present)

### Individual Test Classes

```bash
# Test agent implementation
python -m unittest test_submission.TestAgentCompliance -v

# Test environment
python -m unittest test_submission.TestEnvironmentCompliance -v

# Test grader scoring
python -m unittest test_submission.TestGraderCompliance -v

# Test determinism
python -m unittest test_submission.TestDeterminism -v

# Run benchmark tests (takes longer)
python -m unittest test_submission.TestScoreBenchmarks -v
```

---

## 🔧 Advanced: Run Individual Tasks

### Run Single Task With Scoring

```bash
python scorer.py run --task brute_force --agent baseline --seed 42
```

**Output:**
```
[RUNNING] brute_force with baseline (seed=42)
✓ Score: 0.5234 (success)
```

### Run Full Benchmark for One Agent

```bash
python scorer.py benchmark --agent baseline --seed 42
```

### Compare Multiple Agents

```bash
python scorer.py compare --agents baseline improved_agent v2_agent --seed 42
```

**Output:**
```
================================================================================
AGENT COMPARISON TABLE
================================================================================
Agent                Easy Avg     Medium Avg    Hard Avg     Overall
────────────────────────────────────────────────────────────────────────────────
baseline             0.5234       0.4891       0.3456       0.4527
improved_agent       0.6123       0.5234       0.4123       0.5160
v2_agent             0.7234       0.6234       0.5123       0.6197
================================================================================
```

---

## 📁 Where Scores Are Saved

All scoring results are saved to `artifacts/`:

```
artifacts/
├── benchmark_baseline_2026-04-11_143245.json    ← Raw benchmark results
├── benchmark_improved_2026-04-11_150134.json
├── scorecard_2026-04-11_143245.txt              ← Formatted scorecard
└── unsw_nb15/
    └── metrics.json
```

### Example Benchmark JSON:
```json
{
  "agent_name": "baseline",
  "timestamp": "2026-04-11T14:32:45.123456",
  "total_runs": 3,
  "easy_stats": {
    "difficulty": "easy",
    "task_names": ["brute_force"],
    "scores": [0.5234],
    "avg_score": 0.5234,
    "success_rate": 1.0,
    "success_count": 1,
    "total_runs": 1
  },
  "medium_stats": { ... },
  "hard_stats": { ... },
  "overall_avg_score": 0.4527,
  "overall_success_rate": 0.5
}
```

---

## 💡 Tips for Improving Scores

### Easy Tasks (Score 0.5+)
- Detect threats early (+0.15 response speed bonus)
- Validate all actions before taking them (avoid false positives)
- Complete the mitigation action correctly (+0.25)

### Medium Tasks (Score 0.4+)
- Understand multi-stage attack progression
- Respect stage dependencies (don't skip steps)
- Balance speed with accuracy

### Hard Tasks (Score 0.3+)
- Require at least 3 distinct actions to avoid penalty
- Long observation windows needed for sophisticated detection
- Requires robust reasoning about attack patterns

---

## 🔄 Reproducing Identical Results

All runs use `--seed 42` by default for reproducibility:

```bash
# Run 1
python scoring_script.py --quick --seed 42
# Score: 0.5234

# Run 2 (same seed)
python scoring_script.py --quick --seed 42
# Score: 0.5234 (identical)

# Different seed
python scoring_script.py --quick --seed 123
# Score: 0.4891 (may differ)
```

---

## 📈 Metrics Explanation

### From the Observation object:

```python
observation.recent_auth_logs       # SSH/auth attempts
observation.recent_network_logs    # Network traffic
observation.recent_process_logs    # System processes
observation.blocked_ips            # Your blocked IPs
observation.isolated_hosts         # Your isolated machines
observation.alerts                 # Your raised alerts
observation.active_threat          # Current threat state
```

### From the final metrics dict:

```python
metrics = {
    "attack_detected": bool,           # Did you detect the threat?
    "first_response_tick": int,        # When did you first act?
    "false_positives": int,            # Invalid/irrelevant actions
    "wrong_actions": int,              # Incorrect mitigation attempts
    "decoy_hits": int,                 # Did you hit decoys?
    "stage_misses": int,               # Dependencies violated?
    "correct_actions": int,            # Successful actions
    "actions_taken": list[str],        # Action sequence taken
}
```

---

## ❓ Common Questions

**Q: Why is my hard task score so low?**
A: Hard tasks require sophisticated reasoning. Make sure you're:
1. Taking at least 3 actions (avoid -0.18 penalty)
2. Detecting the exfiltration threat
3. Taking correct mitigation actions
4. Avoiding false positives

**Q: Can I improve the score by just being faster?**
A: Partially. Response speed is +0.15 out of 1.0 max (15%). The other 85% comes from:
- Threat detection (+0.45)
- Correct mitigation (+0.25)
- Difficulty calibration (+0.03-0.10)
- Avoiding penalties (-0.30 to -0.40 per category)

**Q: How do I know if my agent is working correctly?**
A: Run tests first:
```bash
python test_submission.py
```
All should pass. Then check scores increasing with better logic.

**Q: Can I test with different seeds?**
A: Yes! Use `--seed` flag:
```bash
python scoring_script.py --quick --seed 100
python scoring_script.py --quick --seed 200
```
Compare average scores across seeds to ensure robust implementation.

---

## 🎯 Next Steps

1. **First Time**: Run `python scoring_script.py --validate`
2. **Check Results**: Open the scorecard in `artifacts/`
3. **Identify Weak Areas**: Look at which difficulty needs improvement
4. **Iterate**: Modify your agent logic and re-run scoring
5. **Compare**: Use `scorer.py compare` to track improvements

Good luck! 🚀

# Pre-Submission Checklist — Meta Hackathon 2026

**Status:** Last updated April 11, 2026 (1 day before deadline)  
**Deadline:** April 12, 2026, 11:59 PM IST

---

## ⚠️ CRITICAL: All items must PASS or you will be DISQUALIFIED

Your submission will undergo **AUTOMATED VALIDATION** on the hackathon dashboard. The following checks run automatically and block submission if ANY fail:

---

## 📝 Dashboard Checklist Items (Manual Verification)

These checkboxes appear on the submission form. Verify before uploading:

### ✓ I've read the sample inference.py and have followed it strictly

**What judges check:**
- Your `inference.py` must match the structure of the provided sample
- Must use `OpenAI` client (not any other LLM framework)
- Must have `log_start()`, `log_step()`, `log_end()` functions
- Must load environment variables: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
- Must call `env.reset()` and `env.step(action)` from the simulation environment

**Verification:**
```python
# Run after modifications:
python pre_submission_checklist.py
# Look for: ✅ Dashboard Checklist Items > "I've read the sample inference.py and have followed it strictly"
```

### ✓ Environment variables are present in inference.py

**Required variables:**
```python
API_BASE_URL = os.getenv("API_BASE_URL")      # The LLM API endpoint
MODEL_NAME = os.getenv("MODEL_NAME")          # The model identifier
HF_TOKEN = os.getenv("HF_TOKEN")              # Your Hugging Face/API token
```

**Where are they used?**
```python
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# Then:
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=...
)
```

---

## 🤖 Automated Tests (Will run on submission)

These run **without human intervention** when you submit. If ANY fail, your submission is rejected.

### Test 1: HF Space Deployment & Connectivity ✅

**What judges check:**
- Your GitHub repo and HF Space exist
- HF Space URL responds with HTTP 200
- `/reset()` endpoint returns a valid observation
- `/step()` endpoint accepts actions and returns (observation, reward, done, error)

**Before submitting, ensure:**
- [ ] GitHub repo is public
- [ ] HF Space is created and linked
- [ ] Dockerfile exists and builds
- [ ] `inference.py` is in root directory
- [ ] Run: `docker build .` succeeds locally

---

### Test 2: OpenEnv Spec Compliance ✅

**What judges check:**
```yaml
# Your openenv.yaml must have:
name: string
version: string
description: string
tasks:                    # 3+ tasks required
  - name: task1
  - name: task2
  - name: task3

observation_model: {...}  # Pydantic model in YAML
action_model: {...}       # Pydantic model in YAML
reward_model: {...}       # Pydantic model in YAML

grader:
  score_range: [0.0, 1.0]  # CRITICAL: Must be exactly this
```

**Before submitting, verify:**
```bash
python -c "import yaml; yaml.safe_load(open('openenv.yaml'))"
# Should print without errors
```

---

### Test 3: Dockerfile Builds ✅

**What judges check:**
```bash
docker build -t cybersim:latest .
# Must succeed without errors
```

**Your Dockerfile should:**
- [ ] Start with Python 3.9+ base image
- [ ] Copy `requirements.txt` and install: `pip install -r requirements.txt`
- [ ] Copy source code
- [ ] Set working directory
- [ ] Have `CMD` pointing to inference entry point
- [ ] Expose port (if using FastAPI/Flask)

**Common issues:**
- Missing `requirements.txt`
- Wrong dependencies
- Syntax errors in Dockerfile

---

### Test 4: Baseline Reproduces ✅

**What judges check:**
```bash
python inference.py
# Must complete without error and produce scores in [0.0, 1.0] range
```

**Your script must:**
- Load all 3 tasks
- Run each task with your baseline agent
- Produce structured logs
- Output final scores

**Expected output format:**
```
[START] task=brute_force env=<SimulationEnvironment> model=gpt-4o
[STEP] step=1 action=scan_port reward=0.10 done=False error=None
[STEP] step=2 action=exploit reward=0.20 done=False error=None
...
[END] success=True steps=5 score=0.87 rewards=[0.10, 0.20, ...]

[START] task=malware_spread env=<SimulationEnvironment> model=gpt-4o
...
```

---

### Test 5: 3+ Tasks with Graders ✅

**What judges check:**
```bash
# For each task in your openenv.yaml:
from cybersim.tasks.registry import load_task
from cybersim.grader.core import DeterministicGrader

for task_name in ["brute_force", "malware_spread", "data_exfiltration"]:
    task = load_task(task_name)
    grader = DeterministicGrader()
    
    # Run grader on task metrics
    result = grader.evaluate(metrics, success=True)
    
    # Verify:
    assert 0.0 <= result.score <= 1.0  # CRITICAL
```

**Before submitting:**
```bash
python -c "
from cybersim.tasks.registry import available_tasks
print(available_tasks())  # Should have 3+ tasks
"
```

---

## 📋 Mandatory Additional Instructions

### Environment Variables (Set these on HF Spaces)

On your HF Space, add these **Secrets** in the space settings:

| Variable | Value | Example |
|----------|-------|---------|
| `API_BASE_URL` | Your LLM API endpoint | `https://api.openai.com/v1` or `https://api.together.xyz/v1` |
| `MODEL_NAME` | The model identifier | `gpt-4o` or `meta-llama/Llama-2-70b` |
| `HF_TOKEN` | Your API key (keep secret!) | `hf_...` or `sk-...` |

**How to set on HF Spaces:**
1. Go to your Space settings
2. Click "Secrets and optional variables"
3. Add each variable
4. Save

---

### Inference Script Requirements

**Filename:** `inference.py` (exact name, root directory)

**Must contain:**
```python
from openai import OpenAI
import os

# Load variables
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

# Create client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# Implement these functions:
def log_start(task: str, env: object, model: str):
    """Must use exact format: [START] task={task} env={env} model={model}"""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error=None):
    """Must use exact format: [STEP] step={step} action={action} reward={reward:.2f} done={done} error={error}"""
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done} error={error}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list):
    """Must use exact format: [END] success={success} steps={steps} score={score:.2f} rewards={rewards}"""
    print(f"[END] success={success} steps={steps} score={score:.2f} rewards={rewards}", flush=True)

def main():
    # Load all tasks
    # For each task:
    #   1. call env.reset()
    #   2. loop: action = get_model_action() -> env.step(action)
    #   3. grade and log results
    pass

if __name__ == "__main__":
    main()
```

---

### LLM Client Usage

**You MUST use OpenAI Client:**
```python
from openai import OpenAI

client = OpenAI(
    base_url=API_BASE_URL,  # Set on HF Spaces
    api_key=HF_TOKEN        # Set on HF Spaces
)

# Make calls like this:
response = client.chat.completions.create(
    model=MODEL_NAME,  # Set on HF Spaces
    messages=[
        {"role": "system", "content": "You are a cybersecurity agent..."},
        {"role": "user", "content": "Current state: ..."}
    ],
    temperature=0.7,
    max_tokens=100
)

action = response.choices[0].message.content
```

**Do NOT use:**
- ❌ `anthropic.Anthropic()` (Claude)
- ❌ `google.generativeai` (Gemini)
- ❌ Custom HTTP requests to LLM APIs
- ❌ Local models (unless your API_BASE_URL points to them)

---

### Logging Format (STRICT)

Your logs determine how judges evaluate your agent. **ANY deviation = scoring error.**

**Signature 1: Session Start**
```
[START] task={task_name} env={env_object} model={model_name}

✅ CORRECT:   [START] task=brute_force env=<SimulationEnvironment object at 0x...> model=gpt-4o
❌ WRONG:     [START] task=brute_force, env=..., model=...  (extra comma)
❌ WRONG:     [START] TASK=brute_force ... (uppercase key)
❌ WRONG:     START task=brute_force ... (missing brackets)
```

**Signature 2: Each Step**
```
[STEP] step={int} action={action_str} reward={float:.2f} done={bool} error={error_or_none}

✅ CORRECT:   [STEP] step=1 action=scan_port reward=0.10 done=False error=None
❌ WRONG:     [STEP] step=1, action=... (extra comma)
❌ WRONG:     [STEP] step=1 action=scan_port reward=0.1 done=False error=None (reward not .2f)
❌ WRONG:     [STEP] step=1 action='scan_port' ... (quoted action)
```

**Signature 3: Session End**
```
[END] success={bool} steps={int} score={float:.2f} rewards={list}

✅ CORRECT:   [END] success=True steps=5 score=0.87 rewards=[0.10, 0.20, 0.15, 0.22, 0.20]
❌ WRONG:     [END] success=True steps=5 score=0.87 reward=0.87 (wrong key)
❌ WRONG:     [END] success=True steps=5 score=0.87 (missing rewards)
❌ WRONG:     [END] success=True steps=5 score=0.9 (score not .2f format)
```

---

## ⚙️ Infrastructure Restrictions

Your submission must run on judges' hardware:

| Constraint | Limit | Your Status |
|-----------|-------|-------------|
| Runtime | < 20 minutes per task | Test: `time python inference.py` |
| vCPUs | 2 | Docker: 2 parallel processes max |
| Memory | 8 GB | Check task complexity |
| Storage | No requirements | Artifacts may be saved |

**Before submitting, test locally:**
```bash
# Simulate constrained environment
# Measure runtime for all 3 tasks
time python inference.py

# Expected output: 18 min or less total
```

---

## 🚨 Validator Script

**Run this BEFORE submitting — it performs all automated checks locally:**

```bash
python pre_submission_checklist.py
```

**Expected output:**
```
================================================================================
META HACKATHON PRE-SUBMISSION VERIFICATION CHECKLIST
================================================================================

📋 DASHBOARD CHECKLIST ITEMS (Manual Verification)
--------
✅ ✓ Read sample inference.py and followed it strictly
✅ ✓ Environment variables present in inference.py

🤖 AUTOMATED TESTS (Will run on submission)
--------
✅ HF Space Deployment & Connectivity
✅ OpenEnv Spec Compliance
✅ Dockerfile Builds
✅ Inference Script Execution
✅ 3+ Tasks with Graders
✅ Logging Format Compliance
✅ Resource Constraints
✅ Mandatory Variables

================================================================================
VERIFICATION SUMMARY
================================================================================
✅ Passed: 10/10
❌ Failed: 0/10

✅ ALL CHECKS PASSED!

You are ready to submit:
  1. Push to GitHub: git push
  2. Deploy to HF Spaces
  3. Submit HF Space URL to hackathon dashboard
  4. Deadline: 12th April 2026, 11:59 PM IST
```

**If ANY check fails:**
- ❌ Your submission WILL BE REJECTED
- Review the specific failure message
- Fix and re-run: `python pre_submission_checklist.py`
- Repeat until all pass

---

## 📋 Step-by-Step Submission

### Step 1: Verify locally (TODAY)
```bash
# Run the validator
python pre_submission_checklist.py

# Verify all checks pass ✅
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Pre-submission verification complete"
git push
```

### Step 3: Deploy to HF Spaces
```bash
# 1. Create Space on Hugging Face Hub
# 2. Set Secrets (API_BASE_URL, MODEL_NAME, HF_TOKEN)
# 3. Push code: git push huggingface main

huggingface-cli repo create cybersim --type space --space-sdk docker
git push huggingface main
```

### Step 4: Wait for HF Space to build
- Build takes 5-15 minutes
- Check status at: https://huggingface.co/spaces/YOUR_USERNAME/cybersim

### Step 5: Test HF Space URL
```bash
# Verify the Space is running
curl -s https://huggingface.co/spaces/YOUR_USERNAME/cybersim | head

# Should return HTML (200 OK)
```

### Step 6: Submit on hackathon dashboard
- GitHub URL: `https://github.com/YOUR_USERNAME/CyberSim-AI`
- HF Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/cybersim`
- Check both dashboard checklist items ✓
- Click "Submit"

### Step 7: Monitoring
- Dashboard updates with automated test status
- Wait for: "All automated checks PASSED ✅"
- If failures: Review logs, fix, and re-submit

---

## 🆘 Troubleshooting

### ❌ "Dockerfile builds" fails
**Error:** `docker build .` fails locally

**Fix:**
1. Check `requirements.txt` syntax
2. Run `pip install -r requirements.txt` locally to verify
3. Check Dockerfile FOR syntax errors
4. Build again: `docker build .`

### ❌ "Inference Script Execution" fails
**Error:** `python inference.py` produces wrong output or has errors

**Fix:**
1. Run locally: `python inference.py`
2. Check for: `[START]`, `[STEP]`, `[END]` logs
3. Verify exact format (see Logging Format section)
4. Verify environment variables are set:
   ```bash
   export API_BASE_URL="..."
   export MODEL_NAME="..."
   export HF_TOKEN="..."
   python inference.py
   ```

### ❌ "OpenEnv Spec Compliance" fails
**Error:** `openenv.yaml` is invalid

**Fix:**
1. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('openenv.yaml'))"
   ```
2. Check for CRITICAL: `score_range: [0.0, 1.0]`
3. Verify 3+ tasks in tasks list
4. Verify all required fields present

### ❌ "3+ Tasks with Graders" fails
**Error:** One of your graders doesn't work

**Fix:**
```python
# Debug:
from cybersim.grader.core import DeterministicGrader
grader = DeterministicGrader()

test_metrics = {
    "attack_detected": True,
    "difficulty": "medium",
    "first_response_tick": 5,
    "false_positives": 0,
    "wrong_actions": 0,
    "decoy_hits": 0,
    "stage_misses": 0,
    "correct_actions": 1,
    "actions_taken": ["test"],
}

result = grader.evaluate(test_metrics, success=True, max_ticks=32)
print(f"Score: {result.score}")  # Should be 0.0-1.0
```

---

## ✅ Final Checklist (Before Dashboard Submission)

- [ ] `python pre_submission_checklist.py` shows ALL PASSED ✅
- [ ] GitHub repo is public
- [ ] GitHub repo contains all necessary files
- [ ] HF Space created and linked to GitHub
- [ ] HF Space has API_BASE_URL, MODEL_NAME, HF_TOKEN secrets set
- [ ] `inference.py` in root directory
- [ ] `openenv.yaml` has `score_range: [0.0, 1.0]`
- [ ] 3+ tasks defined in `openenv.yaml`
- [ ] All logs use EXACT `[START]`, `[STEP]`, `[END]` format
- [ ] Dockerfile exists and builds
- [ ] `requirements.txt` is complete
- [ ] README.md has setup/submission instructions
- [ ] Test: `time python inference.py` < 20 minutes locally

---

**Last message from the judges:**

> "We will run your submitted GitHub repo code in a Docker container with vcpu=2, memory=8GB. Your inference.py must execute successfully, produce structured logs, and generate valid scores. Ensure all environment variables work, logging is exact, and your agent competes on all 3 tasks."

---

**Deadline: April 12, 2026, 11:59 PM IST** ⏰

**You're almost there! Run the validator, fix any issues, and submit.** 🚀

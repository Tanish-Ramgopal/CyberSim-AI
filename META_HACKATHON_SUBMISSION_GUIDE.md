# Meta Hackathon Submission Guide

**Hackathon:** Meta PyTorch Hackathon 2026  
**Platform:** Scaler School of Technology  
**Submission Deadline:** 12th April 2026, 11:59 PM IST  
**Submission URL:** https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/dashboard

---

## 📋 Quick Checklist Before Submitting

### CRITICAL (Disqualifying if failed):
- [ ] Run `python meta_hackathon_validator.py` — ALL checks must PASS
- [ ] `inference.py` exists in root directory
- [ ] Dockerfile builds successfully
- [ ] `openenv.yaml` is valid with 3+ tasks
- [ ] All environment variables used (API_BASE_URL, MODEL_NAME, HF_TOKEN)
- [ ] Logging uses strict [START], [STEP], [END] format
- [ ] Scores always in [0.0, 1.0] range
- [ ] Baseline inference runs without error (<20 min)

### RECOMMENDED:
- [ ] README.md has all required sections
- [ ] Project deployed to Hugging Face Spaces
- [ ] Tested on resource-constrained machine (vcpu=2, memory=8GB)
- [ ] Runtime confirmed <20 minutes

---

## 🚀 Step 1: Run Pre-Submission Validator

This validates that your submission meets ALL hackathon requirements:

```bash
python meta_hackathon_validator.py
```

**Expected Output:**
```
✅ Passed: 11
❌ Failed: 0
⚠️  Errors: 0

✅ ALL VALIDATIONS PASSED!
   - Push to GitHub
   - Deploy to Hugging Face Spaces
   - Submit the HF Space URL
```

If ANY check fails, fix the issues before submitting!

---

## 🏗️ Step 2: Ensure Project Structure is Correct

Your submission must have:

```
project-root/
├── inference.py                 ← MUST be in root
├── openenv.yaml                 ← MUST be valid
├── Dockerfile                   ← MUST build
├── README.md                    ← Complete documentation
├── requirements.txt             ← All dependencies
├── cybersim/
│   ├── __init__.py
│   ├── models.py               ← Typed Pydantic models
│   ├── environment/
│   │   └── core.py             ← SimulationEnvironment
│   ├── grader/
│   │   ├── spec.py             ← Scoring weights
│   │   └── core.py             ← DeterministicGrader
│   └── tasks/
│       └── registry.py         ← Task loading
├── configs/tasks/
│   ├── brute_force.json        ← Easy task
│   ├── malware_spread.json     ← Medium task
│   └── data_exfiltration.json  ← Hard task
└── server/
    └── app.py                  ← FastAPI server
```

---

## 🔧 Step 3: Verify openenv.yaml

Your `openenv.yaml` MUST include:

```yaml
name: cybersim-ai
version: 0.1.0
description: Your environment description
entrypoint: server/app.py
tasks:
  - brute_force      # Easy
  - malware_spread   # Medium
  - data_exfiltration # Hard
observation_model: cybersim.models.Observation
action_model: cybersim.models.Action
reward_model: cybersim.models.Reward
grader:
  type: deterministic
  score_range: [0.0, 1.0]  # CRITICAL: Must be [0.0, 1.0]
```

---

## 📝 Step 4: Verify inference.py

Your `inference.py` MUST:

1. **Be in the ROOT directory** (not in `scripts/`)
2. **Define environment variables:**
   ```python
   API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
   MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
   HF_TOKEN = os.getenv("HF_TOKEN")
   ```

3. **Use OpenAI Client:**
   ```python
   from openai import OpenAI
   
   if HF_TOKEN:
       client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
   ```

4. **Emit structured logs EXACTLY in this format:**
   ```python
   # STEP 1: START
   print(f"[START] task={task_name} env={env_name} model={model_name}", flush=True)
   
   # STEP 2: STEP (repeated for each action)
   print(f"[STEP] step={step_num} action={action} reward={reward:.2f} done={done} error={error}", flush=True)
   
   # STEP 3: END
   print(f"[END] success={success} steps={num_steps} score={final_score:.2f} rewards={reward_list}", flush=True)
   ```

5. **Handle stdin/stdout properly** for remote execution
6. **Complete in <20 minutes** (use MAX_STEPS=32 default)

### ⚠️ CRITICAL LOGGING FORMAT

The judge's automated system parses ONLY these exact prefixes:
- `[START]` - Episode initialization
- `[STEP]` - Each step taken
- `[END]` - Episode completion

**ANY deviation in format = automatic disqualification**

---

## 🐳 Step 5: Verify Dockerfile

Your Dockerfile MUST:

1. **Use Python 3.10+:**
   ```dockerfile
   FROM python:3.11-slim  # or 3.10, 3.12
   ```

2. **Install dependencies:**
   ```dockerfile
   COPY requirements.txt /app/requirements.txt
   RUN pip install --no-cache-dir -r /app/requirements.txt
   ```

3. **Copy application:**
   ```dockerfile
   COPY . /app
   ```

4. **Expose port (if web service):**
   ```dockerfile
   EXPOSE 7860
   ```

5. **Set working directory:**
   ```dockerfile
   WORKDIR /app
   ```

---

## 📚 Step 6: Update README.md

Your README must include:

### Required Sections:

#### 1. **Project Overview**
```markdown
# CyberSim AI

CyberSim AI is an OpenEnv-style cybersecurity simulation environment for evaluating defensive agents on realistic SOC workflows:
- Detecting SSH brute-force attempts
- Containing malware spread
- Stopping suspicious outbound exfiltration
```

#### 2. **Action Space**
```markdown
## Action Space

The agent can take these actions:
- `block_ip`: Block an IP address to prevent further attacks
- `kill_process`: Terminate a malicious process
- `isolate_machine`: Isolate a host from the network
- `raise_alert`: Escalate to security team
- `noop`: Take no action (used for observation)
```

#### 3. **Observation Space**
```markdown
## Observation Space

Each observation includes:
- `tick`: Current simulation step
- `max_ticks`: Maximum steps allowed
- `objective`: Task goal
- `recent_auth_logs`: Recent authentication attempts
- `recent_network_logs`: Network traffic logs
- `recent_process_logs`: Running processes
- `blocked_ips`: Currently blocked IPs
- `isolated_hosts`: Currently isolated machines
- `alerts`: Raised alerts
```

#### 4. **Grader**
```markdown
## Grader

Scores are from 0.0 to 1.0 based on:

**Bonuses:**
- +0.45: Threat detected
- +0.25: Successful mitigation
- +0.15: Response speed
- +0.10: Difficulty bonus (easy)

**Penalties:**
- -0.12 per false positive (max -0.40)
- -0.12 per wrong action (max -0.40)
- -0.15 per decoy hit (max -0.30)
- -0.15 per missed dependency (max -0.30)
- -0.18 hard task penalty if <3 actions
```

#### 5. **Setup Instructions**
```markdown
## Installation

### Requirements:
- Python 3.10+
- pip

### Setup:
```bash
pip install -r requirements.txt
```

### Run Locally:
```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token"
python inference.py
```

### Run in Docker:
```bash
docker build -t cybersim-ai .
docker run -e HF_TOKEN="your_token" cybersim-ai
```
```

#### 6. **Evaluation Criteria**
```markdown
## Evaluation

Your submission will be judged on:

1. **Runtime Correctness**: Runs without errors
2. **Interface Compliance**: Follows OpenEnv standard
3. **Task Design**: Clear, realistic, testable tasks
4. **Grading Logic**: Reward system is meaningful
5. **Deployment**: Runs on resource-constrained hardware (vcpu=2, memory=8GB)
```

---

## 🚢 Step 7: Deploy to Hugging Face Spaces

1. **Create a Hugging Face account** at https://huggingface.co

2. **Authenticate locally:**
   ```bash
   huggingface-cli login
   # Paste your HF token when prompted
   ```

3. **Create a Space:**
   ```bash
   git clone https://huggingface.co/spaces/your-username/cybersim-ai
   cd cybersim-ai
   ```

4. **Push your code:**
   ```bash
   git add .
   git commit -m "CyberSim AI - Meta Hackathon Submission"
   git push
   ```

5. **Configure Space:**
   - Go to Space Settings
   - Hardware: Select GPU or CPU (CPU works fine)
   - Secrets: Add `HF_TOKEN` environment variable

6. **Get Space URL:**
   ```
   https://huggingface.co/spaces/your-username/cybersim-ai
   ```

---

## ✅ Step 8: Final Checks Before Submission

### Run the validator one more time:
```bash
python meta_hackathon_validator.py
```

### Manually test inference.py:
```bash
export CYBERSIM_TASK="brute_force"
export MAX_STEPS="10"
export HF_TOKEN="test_token"
python inference.py
```

Should see:
```
[START] task=brute_force env=... model=...
[STEP] step=1 action=... reward=0.XX done=false error=null
[STEP] step=2 action=... reward=0.XX done=true error=null
[END] success=true/false steps=2 score=0.XXXX rewards=0.XX,0.XX
```

### Check score format:
```bash
python -c "
import json
# Verify scores are in [0.0, 1.0]
scores = [0.5234, 0.4891, 0.3456]
assert all(0.0 <= s <= 1.0 for s in scores), 'Score out of range'
print('✓ All scores valid')
"
```

---

## 📤 Step 9: Submit

1. **Go to:** https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/dashboard

2. **Click "Submit your Assessment"**

3. **Paste your HF Space URL:**
   ```
   https://huggingface.co/spaces/your-username/cybersim-ai
   ```

4. **Confirm submission** before **12th April 11:59 PM IST**

---

## 🎯 Evaluation Criteria

Your submission will be tested on:

### Pre-Submission Tests (Disqualification if failed):
- [ ] HF Space URL returns 200
- [ ] `reset()` endpoint works
- [ ] OpenEnv spec is valid
- [ ] Dockerfile builds
- [ ] Inference script runs and produces correct [START], [STEP], [END] logs

### Scoring Tests:
- [ ] All 3 tasks run and produce scores
- [ ] Scores are in [0.0, 1.0] range
- [ ] Baseline achieves minimum scores
- [ ] Runtime < 20 minutes

### Quality Assessment:
- [ ] Environment design is realistic and meaningful
- [ ] Grading logic makes sense
- [ ] Baseline agent shows reasonable performance
- [ ] Code quality and documentation

---

## 🚑 Troubleshooting

### "Score out of range [0.0, 1.0]"
- Check `cybersim/grader/spec.py` and `cybersim/grader/core.py`
- Ensure `SCORE_MIN = 0.0` and `SCORE_MAX = 1.0`
- Verify `evaluate()` clamps: `min(1.0, max(0.0, score))`

### "Logging format incorrect"
- Verify exact format: `[START]`, `[STEP]`, `[END]`
- Use `f-string` with `flush=True`
- No extra text outside these lines

### "Dockerfile build fails"
- Ensure `requirements.txt` exists
- Check Python version (3.10+)
- Verify `COPY .` happens after `RUN pip install`

### "Inference script too slow"
- Reduce `MAX_STEPS` (default 32 is fine for test)
- Check LLM API latency
- Consider caching or batching

### "Environment variables not found"
- Ensure all three are used in`inference.py`:
  ```python
  api_url = os.getenv("API_BASE_URL", "...")
  model = os.getenv("MODEL_NAME", "...")
  token = os.getenv("HF_TOKEN")
  ```
- Set them before running OR use defaults

---

## 📞 Support

- **Issues:** Email `help_openenvhackathon@scaler.com`
- **Discord:** Join the hackathon Discord for mentorship
- **Documentation:** See `SCORING_GUIDE.md` for detailed scoring explanation

---

## 🎓 Course Materials

Before submitting, review:
- Module 1: Why OpenEnv? (45 min)
- Module 2: Using Existing Environments (50 min)
- Module 3: Deploying Environments (45 min)
- Module 4: Building Your Own Environment (60 min)

Available at: https://github.com/raun/openenv-course

---

## 🏆 Good Luck!

You have a working, validated submission. Follow the steps above and you'll be ready to submit by the deadline.

**Key Dates:**
- Now - 10th Apr: Build and test
- 11th Apr: Final validation and deployment
- 12th Apr 11:59 PM IST: **DEADLINE**
- 14th & 15th Apr: Results announced

Submit early to allow time for fixes if the automated tests find issues!

---

**Last Updated:** April 2026  
**Status:** Ready for Meta Hackathon Submission

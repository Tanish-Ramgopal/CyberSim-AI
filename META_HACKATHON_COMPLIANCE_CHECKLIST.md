# Meta Hackathon 2026 - Compliance Checklist

**Project:** CyberSim AI  
**Hackathon:** Meta PyTorch Hackathon 2026  
**Deadline:** 12th April 2026, 11:59 PM IST  

---

## ✅ PRE-SUBMISSION VALIDATION

### Run the validator:
```bash
python meta_hackathon_validator.py
```

**Status:** All sections must show ✅ PASSED

---

## 📋 FILE STRUCTURE COMPLIANCE

### Required Files:
- [ ] `inference.py` in root directory
- [ ] `openenv.yaml` with 3+ tasks
- [ ] `Dockerfile` for containerization
- [ ] `README.md` with complete documentation
- [ ] `requirements.txt` with dependencies
- [ ] `cybersim/models.py` (typed Pydantic models)
- [ ] `cybersim/environment/core.py` (SimulationEnvironment)
- [ ] `cybersim/grader/spec.py` (scoring weights)
- [ ] `cybersim/grader/core.py` (DeterministicGrader)
- [ ] `cybersim/tasks/registry.py` (task loading)
- [ ] `configs/tasks/brute_force.json` (easy task)
- [ ] `configs/tasks/malware_spread.json` (medium task)
- [ ] `configs/tasks/data_exfiltration.json` (hard task)
- [ ] `server/app.py` (FastAPI application)

---

## 🔧 MANDATORY ENVIRONMENT VARIABLES

All THREE must be used in `inference.py`:

- [ ] `API_BASE_URL` - Set with default `https://router.huggingface.co/v1`
- [ ] `MODEL_NAME` - Set with default `Qwen/Qwen2.5-72B-Instruct`
- [ ] `HF_TOKEN` - Used for OpenAI client authentication

**Code Check:**
```python
# Must have these lines:
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
```

---

## 🤖 OPENAI CLIENT USAGE

- [ ] Import `from openai import OpenAI`
- [ ] Initialize with HF_TOKEN: `OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)`
- [ ] Use for ALL LLM calls (no other LLM clients allowed)

**Code Check:**
```python
from openai import OpenAI

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
completion = client.chat.completions.create(...)
```

---

## 📝 LOGGING FORMAT COMPLIANCE

### CRITICAL: Structured Output

Your inference script must emit EXACTLY these three log types:

### 1. [START] - Episode Initialization
```
Format: [START] task={task_name} env={environment} model={model_name}
Example: [START] task=brute_force env=cybersim-ai model=Qwen/Qwen2.5-72B-Instruct
```
- [ ] Printed at the start of `main()`
- [ ] Includes task name
- [ ] Includes environment name
- [ ] Includes model name
- [ ] Uses `print(..., flush=True)`

### 2. [STEP] - Each Action Step (repeated)
```
Format: [STEP] step={step_number} action={action_string} reward={reward:.2f} done={bool_value} error={error_or_null}
Example: [STEP] step=1 action=block_ip('192.168.1.100') reward=0.15 done=false error=null
```
- [ ] Printed after each `env.step()`
- [ ] Step number starts at 1
- [ ] Action is string representation
- [ ] Reward is float with 2 decimals
- [ ] Done is lowercase `true` or `false`
- [ ] Error is `null` or error message string
- [ ] Uses `print(..., flush=True)`

### 3. [END] - Episode Completion
```
Format: [END] success={bool} steps={num_steps} score={final_score:.2f} rewards={comma_separated_rewards}
Example: [END] success=true steps=5 score=0.5234 rewards=0.10,0.15,0.20,0.05,0.05
```
- [ ] Printed at the end of episode
- [ ] Success is lowercase `true` or `false`
- [ ] Steps is total number of steps taken
- [ ] Score is final episode score (0.0-1.0) with 2 decimals
- [ ] Rewards are comma-separated floats
- [ ] Uses `print(..., flush=True)`

**Validation Code:**
```bash
# Run inference and check output
python inference.py 2>&1 | grep -E '^\[START\]|\[STEP\]|\[END\]'
```

---

## 📊 SCORING SYSTEM COMPLIANCE

### Score Range
- [ ] All scores must be in `[0.0, 1.0]` range
- [ ] No score should exceed 1.0
- [ ] No score should be below 0.0
- [ ] Use `max(0.0, min(1.0, score))` clamping

**Code Check:**
```python
# In cybersim/grader/spec.py:
SCORE_MIN = 0.0
SCORE_MAX = 1.0

# In cybersim/grader/core.py:
bounded = max(SCORE_MIN, min(SCORE_MAX, round(score, 4)))
```

- [ ] `SCORE_MIN = 0.0`
- [ ] `SCORE_MAX = 1.0`
- [ ] Clamping implemented: `max(0.0, min(1.0, ...))`

### Grading Components
- [ ] Attack detection: +0.45
- [ ] Successful mitigation: +0.25
- [ ] Response speed: +0.0 to +0.15
- [ ] Difficulty bonus: +0.10 (easy), +0.03 (medium), +0.0 (hard)
- [ ] False positive penalties: -0.12 each (capped -0.40)
- [ ] Wrong action penalties: -0.12 each (capped -0.40)
- [ ] Decoy hit penalties: -0.15 each (capped -0.30)
- [ ] Stage miss penalties: -0.15 each (capped -0.30)
- [ ] Hard chain penalty: -0.18 if <3 actions

**File Check:**
```bash
python -c "from cybersim.grader.spec import *; print('✓ Weights loaded')"
```

---

## 🎯 TASK REQUIREMENTS

### Minimum 3 Tasks
- [ ] `brute_force` - Easy difficulty
- [ ] `malware_spread` - Medium difficulty
- [ ] `data_exfiltration` - Hard difficulty

### Task Properties
- [ ] Each has unique objective
- [ ] Each has clear difficulty level
- [ ] Each has associated config file in `configs/tasks/`
- [ ] Each can be loaded via `load_task(name)`
- [ ] Each has working grader

**Code Check:**
```python
from cybersim.tasks.registry import load_task, available_tasks
for task_name in available_tasks():
    task = load_task(task_name)
    print(f"{task_name}: {task['difficulty']}")
```

---

## 🏗️ OPENENV SPEC COMPLIANCE

### openenv.yaml Structure
- [ ] `name:` - Environment name
- [ ] `version:` - Semantic version
- [ ] `description:` - What it does
- [ ] `entrypoint:` - Server entry point
- [ ] `tasks:` - List of task names (3+)
- [ ] `observation_model:` - Path to Observation class
- [ ] `action_model:` - Path to Action class
- [ ] `reward_model:` - Path to Reward class
- [ ] `episode.termination` - When episode ends
- [ ] `grader.type` - "deterministic"
- [ ] `grader.score_range` - [0.0, 1.0]
- [ ] `reproducibility.deterministic_with_seed` - true

**File Check:**
```bash
python -c "
import yaml
with open('openenv.yaml') as f:
    config = yaml.safe_load(f)
    assert config['grader']['score_range'] == [0.0, 1.0]
    assert len(config['tasks']) >= 3
    print('✓ openenv.yaml valid')
"
```

---

## 🐳 DOCKER COMPLIANCE

### Dockerfile Requirements
- [ ] Use Python 3.10+ image
- [ ] Set `WORKDIR`
- [ ] Copy `requirements.txt`
- [ ] Run `pip install --no-cache-dir`
- [ ] Copy application code
- [ ] Set `PYTHONUNBUFFERED=1`
- [ ] Expose port (if applicable)
- [ ] Define `CMD` or `ENTRYPOINT`

**Build Check:**
```bash
docker build -t cybersim-ai . && echo "✓ Dockerfile builds"
```

---

## 📚 README COMPLIANCE

### Required Sections
- [ ] **Project Title**
- [ ] **Overview** - What the environment does
- [ ] **Motivation** - Why it's important
- [ ] **Action Space** - Available actions
- [ ] **Observation Space** - Observation fields
- [ ] **Tasks** - Description of all 3+ tasks
- [ ] **Grader** - Scoring rubric
- [ ] **Installation** - How to set up
- [ ] **Usage** - How to run locally
- [ ] **Docker** - How to containerize
- [ ] **Evaluation** - How submissions are judged
- [ ] **Results** - Sample outputs

**Validation:**
```bash
# Check README sections
grep -i "## Action\|## Observation\|## Grader\|## Installation" README.md
```

---

## ⚡ PERFORMANCE REQUIREMENTS

### Runtime Constraints
- [ ] Inference script completes in **< 20 minutes**
- [ ] Default `MAX_STEPS = 32` (reasonable)
- [ ] Uses `flush=True` for immediate log output
- [ ] No blocking operations

**Code Check:**
```bash
# Test runtime with limited steps
time python inference.py
# Should complete in seconds (full run in <20 min)
```

### Resource Requirements
- [ ] Works on **vcpu=2, memory=8GB** machine
- [ ] Docker image is reasonably sized
- [ ] No excessive dependencies
- [ ] No GPU required (optional, not assumed)

**Check:**
```bash
# Verify dependencies are reasonable
wc -l requirements.txt  # Should be <50 lines for baseline
docker images cybersim-ai  # Check image size
```

---

## 🔗 HUGGING FACE SPACES DEPLOYMENT

### Space Configuration
- [ ] Space URL: `https://huggingface.co/spaces/your-username/cybersim-ai`
- [ ] SDK: Docker
- [ ] Authentication: HF_TOKEN secret configured
- [ ] Endpoint responds to: `/reset`, `/step`, `/state`
- [ ] Returns HTTP 200

**Verification:**
```bash
curl -X POST https://huggingface.co/spaces/your-username/cybersim-ai/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "brute_force", "seed": 42}'
# Should return 200 with valid observation
```

---

## 🎬 TESTING CHECKLIST

### Local Testing
- [ ] Run `python meta_hackathon_validator.py` → All PASS
- [ ] Run `python inference.py` → Produces [START]/[STEP]/[END]
- [ ] Run `docker build .` → Builds successfully
- [ ] Score output is in [0.0, 1.0] range

### Task Testing
- [ ] `brute_force` task runs and scores
- [ ] `malware_spread` task runs and scores
- [ ] `data_exfiltration` task runs and scores
- [ ] Grader returns valid results for all tasks

**Run Tests:**
```bash
# Validate all components
python -m unittest discover -s tests -p "test_*.py"
```

### Logging Testing
- [ ] Exactly 1 [START] line per run
- [ ] Multiple [STEP] lines (one per step)
- [ ] Exactly 1 [END] line per run
- [ ] No extra output outside these lines

**Check:**
```bash
python inference.py 2>&1 | head -20
python inference.py 2>&1 | tail -5
```

---

## 📤 SUBMISSION STEPS

### Before Submission:
1. [ ] Run `python meta_hackathon_validator.py` → All PASS
2. [ ] Verify `inference.py` is in root
3. [ ] Check `openenv.yaml` has score_range [0.0, 1.0]
4. [ ] Confirm all 3 tasks present with graders
5. [ ] Test Dockerfile builds
6. [ ] Deploy to Hugging Face Spaces
7. [ ] Verify HF Space endpoint is accessible

### Submission:
1. [ ] Go to Meta Hackathon Dashboard
2. [ ] Click "Submit your Assessment"
3. [ ] Paste HF Space URL
4. [ ] Choose "Solo" or "Team" (if team, only lead submits)
5. [ ] Click "Submit"
6. [ ] Confirm submission received

### Deadline:
- [ ] Submitted by **12th April 2026, 11:59 PM IST**

---

## 🚨 CRITICAL FAILURE POINTS

These will result in **AUTOMATIC DISQUALIFICATION**:

- [ ] Missing or incorrect [START]/[STEP]/[END] logging
- [ ] Score out of [0.0, 1.0] range
- [ ] Fewer than 3 tasks with graders
- [ ] `openenv.yaml` missing or invalid
- [ ] Dockerfile fails to build
- [ ] `inference.py` not in root directory
- [ ] Environment variables not properly used
- [ ] Not using OpenAI client for LLM calls
- [ ] Inference script times out (>20 min)
- [ ] Submission after deadline

---

## ✅ FINAL CHECKLIST

```
□ All required files present
□ Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN
□ OpenAI client properly initialized
□ Logging format: exact [START]/[STEP]/[END]
□ Scoring: [0.0, 1.0] range
□ 3+ tasks with graders
□ openenv.yaml with score_range [0.0, 1.0]
□ Dockerfile builds successfully
□ README has all required sections
□ Inference runs in <20 minutes
□ Deployed to HF Spaces
□ Validator passes all checks
□ Submitted before deadline
```

---

## 📞 SUPPORT

- **Validator:** `python meta_hackathon_validator.py`
- **Submission:** https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/dashboard
- **Questions:** help_openenvhackathon@scaler.com
- **Discord:** Join for mentorship and community

---

**Last Updated:** April 2026  
**Status:** ✅ Ready for Submission

# How to Test Your Project — Complete Testing Guide

## The 3 Ways to Get Scores

### 1️⃣ **LOCAL TESTING (No API Key Needed)** — What you did above
```bash
python run_simulation.py --task brute_force --agent baseline --seed 42
```

**Result:** You see scores immediately
- Easy: 0.9167
- Medium: 0.8527
- Hard: 0.6513

**Why?** Your `baseline` agent is **hardcoded** to make good decisions. It doesn't call any API.

---

### 2️⃣ **WITH LLM AGENT (Needs API Key)** — What your friends do
```bash
python run_simulation.py --task brute_force --agent llm --seed 42
```

**Before running this, set:**
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="sk-..."  # Your OpenAI API key
```

**What happens:**
1. Simulation runs
2. Agent calls LLM API (costs $$ per call!)
3. LLM decides actions → agents make different decisions each time
4. Scores change based on LLM response quality
5. Your friends see scores like: 0.85, 0.92, 0.71 (all different!)

**Why vary?** LLM responses are non-deterministic (random). Same prompt = different answers sometimes.

---

### 3️⃣ **JUDGES TESTING (On Hugging Face Spaces)**
```bash
python inference.py
```

Run on HF Spaces with:
- Your submission code
- API_BASE_URL, MODEL_NAME, HF_TOKEN set as **secrets**
- Your LLM agent running

**Judges do:**
1. Clone your GitHub repo
2. Build Docker container
3. Set environment variables (API keys in HF Space secrets)
4. Run `python inference.py`
5. Parse `[START]`, `[STEP]`, `[END]` logs
6. Calculate final scores
7. Compare with other teams

---

## Why Scores Are Different Each Time

### Scenario: Your friend runs with LLM agent

**Run 1:**
```bash
python run_simulation.py --task brute_force --agent llm --seed 42
```
LLM response:
```
{action_type: "block_ip", target: "203.0.113.66"}
Score: 0.92
```

**Run 2:** Same command, SAME seed
```bash
python run_simulation.py --task brute_force --agent llm --seed 42
```
LLM response:
```
{action_type: "isolate_machine", target: "auth-srv-01"}
Score: 0.78
```

**Why different?**
- Same task (seed=42 = same threat scenario)
- Different LLM response (LLM is probabilistic)
- Different actions → different scores

---

## The Complete Testing Workflow

### Step 1: Local Testing (Baseline Agent - No Cost)
Use this **whenever you want to test fast**:

```bash
# Test all 3 difficulties
python run_simulation.py --task brute_force --agent baseline --seed 42
python run_simulation.py --task malware_spread --agent baseline --seed 42
python run_simulation.py --task data_exfiltration --agent baseline --seed 42
```

**Cost:** Free  
**Time:** 1 minute  
**Scores:** Always the same (deterministic)

---

### Step 2: Testing with Your LLM Agent (Costs $$)
Use this **before final submission** to verify your agent works:

**Setup Once:**
```bash
# Add your actual API key
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"  # or your chosen model
export HF_TOKEN="sk_..."          # Your OpenAI key
```

**Test:**
```bash
# Test with LLM agent
python run_simulation.py --task brute_force --agent llm --seed 42 --show-logs
python run_simulation.py --task malware_spread --agent llm --seed 42 --show-logs
python run_simulation.py --task data_exfiltration --agent llm --seed 42 --show-logs
```

**Cost:** $0.05-$0.50 per task (OpenAI API charges)  
**Time:** 2-5 minutes per task  
**Scores:** Vary each time (probabilistic)

---

### Step 3: Pre-Submission Validation (No Cost)
Before submitting to judges:

```bash
python pre_submission_checklist.py
```

This validates:
- ✅ inference.py format
- ✅ Environment variables present
- ✅ Logging format correct
- ✅ All 3 tasks runnable
- ✅ Scores in [0.0, 1.0] range

---

### Step 4: Deploy to HF Spaces
1. Create Space on Hugging Face
2. Add secrets:
   - `API_BASE_URL` = your actual endpoint
   - `MODEL_NAME` = your actual model
   - `HF_TOKEN` = your actual key
3. Push code: `git push huggingface main`

---

### Step 5: Judges Run (Automated)
Judges:
1. Deploy your repo to HF Spaces
2. Run: `python inference.py`
3. Parse logs and calculate scores
4. Compare with other teams
5. Rank submissions

---

## Why Your Friends See Different Scores

**Friend's Explanation:**
> "This time the scores are high (0.92), this time they are low (0.71)"

**What's happening:**
1. She has an LLM agent (using OpenAI API)
2. She runs: `python run_simulation.py --task brute_force --agent llm`
3. LLM gives different responses each time
4. Same scenario, different actions → different scores

**You can reproduce this:**
```bash
# Set your API key first
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="sk_..."

# Run multiple times - scores will vary
python run_simulation.py --task brute_force --agent llm --seed 42
python run_simulation.py --task brute_force --agent llm --seed 42
python run_simulation.py --task brute_force --agent llm --seed 42
```

Each run gives different score because LLM is non-deterministic!

---

## How Judges Test (The Real Submission)

### What Judges Do:
```bash
# 1. Clone your repo
git clone https://github.com/YOUR_USERNAME/CyberSim-AI

# 2. Build Docker image
docker build -t cybersim .

# 3. Run container with secrets set
docker run \
  -e API_BASE_URL="https://..." \
  -e MODEL_NAME="gpt-4o" \
  -e HF_TOKEN="hf_..." \
  cybersim python inference.py
```

### What They Expect:
```
[START] task=brute_force env=<SimulationEnvironment> model=gpt-4o
[STEP] step=1 action=scan_port reward=0.10 done=False error=None
[STEP] step=2 action=block_ip reward=0.20 done=False error=None
...
[END] success=True steps=5 score=0.87 rewards=[0.10, 0.20, ...]
```

### They Calculate:
- Extract `score` from `[END]` log
- Verify score is in [0.0, 1.0]
- Compare across all submissions
- Rank teams

---

## Quick Testing Commands

### Test Baseline Agent (Free, Fast)
```bash
# Easy
python run_simulation.py --task brute_force --agent baseline --seed 42

# Medium
python run_simulation.py --task malware_spread --agent baseline --seed 42

# Hard
python run_simulation.py --task data_exfiltration --agent baseline --seed 42
```

### Test with Your LLM Agent (Costs $$)
```bash
# First set your API key
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="sk_YOUR_ACTUAL_KEY"

# Then test
python run_simulation.py --task brute_force --agent llm --seed 42 --show-logs
```

### See Detailed Logs
```bash
python run_simulation.py --task brute_force --agent baseline --seed 42 --show-logs
```

### Get Scores in JSON Format
```bash
python run_simulation.py --task brute_force --agent baseline --seed 42 > score.json
cat score.json
```

---

## FAQ: Understanding the Scores

### Q: Why do my scores change?
**A:** If using LLM agent, LLM responses vary. If using baseline agent, they should be identical every time.

### Q: Should I use API key for testing?
**A:** 
- ✅ YES: Before final submission (to verify LLM integration works)
- ❌ NO: During development (baseline agent is fine, saves money)

### Q: How much does it cost to test with LLM?
**A:**
- gpt-4o-mini: ~$0.05-$0.15 per task
- gpt-4o: ~$0.50-$1.00 per task
- Other models: varies

### Q: Will judges use my API key?
**A:** NO. They use their own. Your HF Space secrets are your credentials, judges' credentials are separate.

### Q: Why do friends get different scores?
**A:** They test multiple times with LLM agent. Each time, LLM gives different response → different score.

### Q: How should I compare my agent to friends?
**A:** Run with same seed, same model, same API provider:
```bash
# Both of you run this
python run_simulation.py --task brute_force --agent llm --seed 42
# Then average scores over multiple runs
```

---

## Your Testing Checklist

- [ ] Test with baseline agent (free, instant)
  ```bash
  python run_simulation.py --task brute_force --agent baseline --seed 42
  ```

- [ ] Run pre-submission validator
  ```bash
  python pre_submission_checklist.py
  ```

- [ ] Test with LLM agent (optional, with API key)
  ```bash
  export API_BASE_URL="..."
  export HF_TOKEN="sk_..."
  python run_simulation.py --task brute_force --agent llm --seed 42
  ```

- [ ] Deploy to HF Spaces
  ```bash
  git push huggingface main
  ```

- [ ] Verify HF Space runs inference
  ```bash
  curl https://huggingface.co/spaces/YOUR_USERNAME/cybersim
  ```

- [ ] Submit GitHub + HF Space URLs to dashboard

---

## TL;DR

| Test Type | Command | Cost | Result Varies? | Use When |
|-----------|---------|------|---|---|
| **Baseline** | `python run_simulation.py --task brute_force --agent baseline --seed 42` | Free | No (same every time) | Development, testing infrastructure |
| **LLM Agent** | `python run_simulation.py --task brute_force --agent llm --seed 42` | $$ | Yes (LLM is random) | Final verification before submission |
| **HF Spaces** | `python inference.py` (on HF Space) | Your credits | Yes (judges test) | Actual submission |

**Your friends' scores vary** because they test with LLM agent multiple times. **Judges will test** by running inference.py on your HF Space with their own credentials. **You should test** with baseline first (free), then LLM agent once (to verify), then submit.

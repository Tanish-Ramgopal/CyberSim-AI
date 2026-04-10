# Testing Flow Diagram

```
YOUR PROJECT TESTING PIPELINE
═════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ YOU — During Development & Testing                      │
└─────────────────────────────────────────────────────────┘

    ⬇️

┌──────────────────────────────────────────────────────────────┐
│ LOCAL TEST #1: Baseline Agent (FREE, NO API KEY)             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Command: python run_simulation.py --task brute_force \      │
│           --agent baseline --seed 42                         │
│                                                               │
│  What Happens:                                               │
│  • Simulation runs                                           │
│  • Baseline agent makes pre-defined good decisions          │
│  • NO API CALLS (no cost)                                   │
│  • Score: 0.9167 (ALWAYS SAME)                             │
│                                                               │
│  Use This: ✅ During development, testing infrastructure    │
│  Cost:     🟢 FREE                                          │
│  Time:     ⚡ 30 seconds                                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘

    ⬇️ (Optional - before final submission)

┌──────────────────────────────────────────────────────────────┐
│ LOCAL TEST #2: LLM Agent (COSTS $$, NEEDS API KEY)           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Setup: export API_BASE_URL="https://api.openai.com/v1"    │
│         export MODEL_NAME="gpt-4o-mini"                     │
│         export HF_TOKEN="sk_..."                            │
│                                                               │
│  Command: python run_simulation.py --task brute_force \      │
│           --agent llm --seed 42                             │
│                                                               │
│  What Happens:                                               │
│  • Simulation runs                                           │
│  • Agent calls LLM API (uses your API key)                  │
│  • LLM responds with action decision                        │
│  • API CALL COSTS MONEY ($0.05-$1.00 per task)            │
│  • Score: 0.85, 0.92, 0.71 (VARIES each run!)             │
│                                                               │
│  WHY SCORES VARY?                                            │
│  → Same scenario (seed=42)                                  │
│  → Different LLM response → different action                │
│  → Different action → different score                       │
│                                                               │
│  Use This: ✅ Final verification before deployment         │
│  Cost:     🔴 COSTS MONEY                                  │
│  Time:     ⏱️  2-5 minutes per task                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘

    ⬇️

┌──────────────────────────────────────────────────────────────┐
│ VALIDATION: Pre-Submission Checker (FREE)                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Command: python pre_submission_checklist.py                │
│                                                               │
│  Validates:                                                  │
│  ✅ inference.py format correct                             │
│  ✅ Environment variables present                           │
│  ✅ Logging format [START], [STEP], [END]                  │
│  ✅ All 3 tasks runnable                                    │
│  ✅ Scores in [0.0, 1.0] range                             │
│  ✅ Dockerfile builds                                       │
│  ✅ openenv.yaml compliant                                  │
│                                                               │
│  Use This: ✅ Before submitting to judges                  │
│  Cost:     🟢 FREE                                          │
│  Time:     ⚡ 2 minutes                                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘

    ⬇️

┌──────────────────────────────────────────────────────────────┐
│ DEPLOYMENT: Upload to Hugging Face Spaces                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Create HF Space (Space SDK: Docker)                      │
│  2. Set Secrets:                                             │
│     • API_BASE_URL = https://api.openai.com/v1             │
│     • MODEL_NAME = gpt-4o                                   │
│     • HF_TOKEN = your_actual_key                            │
│  3. Push code: git push huggingface main                     │
│  4. Wait 5-15 minutes for build                             │
│  5. Verify Space is running                                 │
│                                                               │
│  Use This: ✅ For judges to run your submission            │
│                                                               │
└──────────────────────────────────────────────────────────────┘

    ⬇️

┌─────────────────────────────────────────────────────────────┐
│ JUDGES — On April 13+                                       │
└─────────────────────────────────────────────────────────────┘

    ⬇️

┌──────────────────────────────────────────────────────────────┐
│ AUTOMATED TEST: Judges Run Your Submission                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  What Judges Do:                                             │
│  1. Clone: git clone https://github.com/YOUR/REPO          │
│  2. Build: docker build -t cybersim .                       │
│  3. Run: docker run -e API_BASE_URL="..." \                 │
│          -e MODEL_NAME="..." \                              │
│          -e HF_TOKEN="..." \                                │
│          cybersim python inference.py                        │
│  4. Parse logs: Extract [START], [STEP], [END]             │
│  5. Calculate score                                          │
│  6. Compare with other teams                                │
│  7. Rank submissions                                         │
│                                                               │
│  They Use: 🟢 THEIR OWN API KEYS                            │
│  Your Cost: ❌ YOU DON'T PAY ANYTHING                       │
│  Score: Varies based on LLM response to scenario            │
│                                                               │
└──────────────────────────────────────────────────────────────┘

    ⬇️

┌─────────────────────────────────────────────────────────────┐
│ RESULTS: Scores & Rankings                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Why Your Friend's Scores Vary

```
Friend's Testing Pattern:
═══════════════════════════

Run 1:
  Command: python run_simulation.py --task brute_force --agent llm --seed 42
  Scenario: Brute force attack (same every time, seed=42)
  LLM Response 1: "block_ip -target 203.0.113.66"
  Result: Score 0.92

Run 2:
  Command: python run_simulation.py --task brute_force --agent llm --seed 42
  Scenario: Brute force attack (same every time, seed=42)
  LLM Response 2: "isolate_machine -target auth-srv-01"
  Result: Score 0.78

Run 3:
  Command: python run_simulation.py --task brute_force --agent llm --seed 42
  Scenario: Brute force attack (same every time, seed=42)
  LLM Response 3: "noop"
  Result: Score 0.45

→ Same scenario, different LLM responses = different scores
→ LLM is probabilistic (non-deterministic)
```

---

## How to Compare Your Agent with Friends

```bash
# Both of you run with SAME seed, SAME model, SAME settings
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="sk_..."

# Run multiple times and average
for i in {1..3}; do
  python run_simulation.py --task brute_force --agent llm --seed 42
done

# Average the 3 scores to get a comparable baseline
```

---

## Cost Comparison

```
Test Type              Cost    API Calls    Use For
──────────────────────────────────────────────────────────
Baseline Agent         FREE    0            • Development
                                           • Testing infra
                                           • Quick validation

LLM Agent              $$      Yes          • Final test
                       $0.05-  Per run      • Before submit
                       $1.00   (1 per task)

HF Spaces Deploy       FREE    Depends      • Judges evaluate
                                on judges   • Official scoring
                                run

Judge Evaluation       Judges' N/A          • Final ranking
                       cost    (their       • Leaderboard
                               creds)
```

---

## Quick Reference: What Should You Do?

### Week of Submission (April 11-12):

```
┌─ Monday (April 11)
│  └─ Run: python pre_submission_checklist.py ✅
│  └─ Scores: Easy 0.92, Medium 0.85, Hard 0.65
│  └─ Status: GOOD (all 10 checks pass)
│
├─ Day Before Submission (April 12)
│  └─ (Optional) Test LLM agent: python run_simulation.py --agent llm
│  └─ Verify inference.py works with actual LLM
│  └─ Check logs format
│
└─ Submission Day (April 12)
   └─ Push to GitHub
   └─ Deploy to HF Spaces
   └─ Submit URLs to dashboard
   └─ WAIT for judges (April 13+)
```

---

## TL;DR Summary

| When | Tool | Command | Cost | Score Varies? |
|------|------|---------|------|---------------|
| **Development** | Baseline Agent | `python run_simulation.py --agent baseline --seed 42` | FREE | ❌ No |
| **Pre-Submit** | LLM Agent (optional) | `python run_simulation.py --agent llm --seed 42` | $$ | ✅ Yes |
| **Final Check** | Pre-Submission | `python pre_submission_checklist.py` | FREE | N/A |
| **Official** | Judges (HF Spaces) | `python inference.py` | Judges | ✅ Yes |

**Your friends see different scores** = they test LLM agent multiple times = LLM varies  
**Judges will evaluate** = they run your inference.py = LLM + your code + their credentials  
**You should** = test baseline locally (free) → validate with checker → deploy to HF → submit

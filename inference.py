"""
CyberSim AI - Judge-Facing LLM-Powered Cybersecurity Agent

This script runs a cybersecurity agent powered by an LLM through simulated attack scenarios.
The agent must detect and mitigate threats in real-time. Scores are computed by DeterministicGrader
based on detection speed, accuracy, and proper mitigation actions.

Required Environment Variables:
  - API_BASE_URL: LLM API endpoint (e.g., https://api.openai.com/v1)
  - MODEL_NAME: Model identifier (e.g., gpt-4o-mini)
  - HF_TOKEN: API authentication token (OpenAI key, HF token, or similar)

Output Format (strictly enforced):
  [START] task=<task> env=<environment> model=<model>
  [STEP] step=<n> action=<action> reward=<reward:.2f> done=<bool> error=<error>
  [END] success=<bool> steps=<n> score=<score:.2f> rewards=<list>
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import List, Optional

from openai import OpenAI

from cybersim.environment.core import SimulationEnvironment
from cybersim.grader.core import DeterministicGrader
from cybersim.models import Action, Observation
from cybersim.tasks.registry import load_task


# ==============================================================================
# Configuration: Environment Variables
# ==============================================================================

# LLM Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
"""LLM API endpoint URL. Required for inference."""

MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
"""Model identifier for LLM calls. Required for inference."""

HF_TOKEN = os.getenv("HF_TOKEN")
"""Authentication token for LLM API. Required for inference."""

# Simulation Configuration
TASK_NAME = os.getenv("CYBERSIM_TASK", "brute_force")
"""Which cybersecurity scenario to run: brute_force, malware_spread, or data_exfiltration."""

SEED = int(os.getenv("SEED", "42"))
"""Random seed for reproducibility."""

MAX_STEPS = int(os.getenv("MAX_STEPS", "32"))
"""Maximum simulation steps before timeout."""

# Execution Configuration
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
"""LLM temperature: 0.0 = deterministic, higher = more random."""

BENCHMARK = os.getenv("CYBERSIM_BENCHMARK", "cybersim-ai")
"""Benchmark name for identification."""

CYBERSIM_ENV_URL = os.getenv("CYBERSIM_ENV_URL")
"""Optional: External environment service URL (for distributed evaluation)."""

LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
"""Optional: Local Docker image name."""


# ==============================================================================
# Logging Functions: Judge-Enforced Output Format
# ==============================================================================

def _single_line(value: str) -> str:
    """
    Convert multi-line text to single line by collapsing whitespace.
    
    Args:
        value: Potentially multi-line string
        
    Returns:
        Single-line string with normalized whitespace
    """
    return re.sub(r"\s+", " ", value).strip()


def log_start(task: str, env: str, model: str) -> None:
    """
    Log session initialization.
    
    Format: [START] task=<task> env=<environment> model=<model>
    
    Args:
        task: Task name (brute_force, malware_spread, data_exfiltration)
        env: Environment identifier (e.g., cybersim-ai)
        model: LLM model name
    """
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """
    Log each simulation step.
    
    Format: [STEP] step=<n> action=<action> reward=<reward:.2f> done=<bool> error=<error>
    
    Args:
        step: Step number (1-indexed)
        action: Action taken by agent
        reward: Immediate reward from this step
        done: Whether episode completed
        error: Error message if step failed (None = no error)
    """
    done_val = str(done).lower()
    error_val = "null" if error is None else _single_line(error)
    action_val = _single_line(action)
    print(
        f"[STEP] step={step} action={action_val} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """
    Log session completion with final score.
    
    Format: [END] success=<bool> steps=<n> score=<score:.2f> rewards=<list>
    
    Args:
        success: Whether the task was completed successfully
        steps: Total steps taken
        score: Final score in range [0.0, 1.0] from DeterministicGrader
        rewards: List of per-step rewards
    """
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ==============================================================================
# LLM Integration: Prompt Building & Model Inference
# ==============================================================================

def build_user_prompt(observation: Observation) -> str:
    """
    Build JSON prompt for LLM from environment observation.
    
    The LLM receives a complete view of the current cyber threat landscape:
    - Detected threats and their characteristics
    - Recent system logs (authentication, network, process)
    - Current defensive actions in place (blocked IPs, isolated hosts)
    - Available response actions
    
    Args:
        observation: Current environment observation from simulator
        
    Returns:
        JSON-formatted prompt containing threat state and action requirements
    """
    payload = {
        # Objective: what the agent is trying to achieve
        "objective": observation.objective,
        # Time: current step and maximum steps
        "tick": observation.tick,
        "max_ticks": observation.max_ticks,
        # Threat intelligence: what threats are detected
        "possible_threats": observation.possible_threats,
        # System logs: audit trail for detection
        "recent_auth_logs": observation.recent_auth_logs,
        "recent_network_logs": observation.recent_network_logs,
        "recent_process_logs": observation.recent_process_logs,
        # Current defensive state
        "blocked_ips": observation.blocked_ips,
        "isolated_hosts": observation.isolated_hosts,
        # Action space: what the agent can do
        "allowed_actions": ["block_ip", "kill_process", "isolate_machine", "raise_alert", "noop"],
        # JSON schema: what format LLM must return
        "required_json": {
            "action_type": "one of: block_ip, kill_process, isolate_machine, raise_alert, noop",
            "target": "IP address or hostname or alert name (string)"
        },
    }
    return json.dumps(payload, indent=2)


def get_model_action(client: Optional[OpenAI], observation: Observation) -> Action:
    """
    Query LLM to get next action.
    
    The agent receives the threat landscape and decides what defensive action
    to take. Valid actions:
    - block_ip: Block traffic from a suspicious IP
    - kill_process: Terminate a malicious process
    - isolate_machine: Disconnect a compromised host
    - raise_alert: Escalate to security team
    - noop: Do nothing this step
    
    Args:
        client: OpenAI client (or None if token missing)
        observation: Current environment state
        
    Returns:
        Action object containing action_type and target
    """
    # Handle missing API client
    if client is None:
        return Action(action_type="noop", target="none")
    
    try:
        # Query LLM for decision
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity SOC (Security Operations Center) agent. "
                        "You must detect threats and respond with mitigation actions. "
                        "Your response MUST be valid JSON with exactly these keys: action_type, target. "
                        "Do NOT include markdown, explanations, or extra text. "
                        "Return ONLY the JSON object."
                    ),
                },
                {
                    "role": "user",
                    "content": build_user_prompt(observation)
                },
            ],
        )
        
        # Parse LLM response
        text = (completion.choices[0].message.content or "").strip()
        data = json.loads(text)
        return Action(
            action_type=data.get("action_type", "noop"),
            target=data.get("target", "none")
        )
    
    except Exception:
        # Fallback to noop if LLM fails (malformed response, API error, etc.)
        return Action(action_type="noop", target="none")


# ==============================================================================
# Environment Communication: Local & Remote
# ==============================================================================

def _http_json(method: str, url: str, payload: Optional[dict] = None) -> dict:
    """
    Make HTTP request to environment service (for distributed evaluation).
    
    Used when CYBERSIM_ENV_URL is set (judges may use remote evaluation).
    For local runs, uses in-memory SimulationEnvironment instead.
    
    Args:
        method: HTTP method (POST, GET, etc.)
        url: Full URL to environment endpoint
        payload: JSON request body
        
    Returns:
        Parsed JSON response as dictionary
    """
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ==============================================================================
# Main Evaluation Loop
# ==============================================================================

def main() -> None:
    """
    Main evaluation loop: run agent through cybersecurity scenario.
    
    1. Initialize environment (task scenario)
    2. Reset environment to initial state
    3. Loop: observe -> decide -> act -> receive feedback
    4. Grade performance using DeterministicGrader
    5. Output strict [START]/[STEP]/[END] format
    
    Environment Variables:
      - HF_TOKEN: If missing, logs error and agent defaultsides to noop
      - API_BASE_URL, MODEL_NAME: LLM configuration
      - CYBERSIM_ENV_URL: If set, uses remote HTTP environment (else local)
      - MAX_STEPS, SEED: Simulation parameters
    
    Output:
      Prints strictly-formatted logs that judges parse for scoring.
      Any deviation in format causes evaluation failure.
    """
    
    # ========== Initialization ==========
    task = load_task(TASK_NAME)
    env = SimulationEnvironment(task, seed=SEED) if not CYBERSIM_ENV_URL else None
    grader = DeterministicGrader()
    
    # State tracking for scoring
    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    last_error: Optional[str] = None
    
    # Signal that evaluation started
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    
    # LLM client initialization
    client: Optional[OpenAI] = None
    
    try:
        # ========== Setup LLM Client ==========
        # OpenAI client is REQUIRED interface for all LLM calls.
        # Judges will provide API credentials via HF_TOKEN environment variable.
        if HF_TOKEN:
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
        else:
            last_error = "missing HF_TOKEN: cannot initialize LLM client"
        
        # ========== Initialize Environment ==========
        # Two modes: Local (in-process) or Remote (HTTP)
        if CYBERSIM_ENV_URL:
            # Remote evaluation: communicate via HTTP
            base = CYBERSIM_ENV_URL.rstrip("/")
            reset_data = _http_json("POST", f"{base}/reset", {"task": TASK_NAME, "seed": SEED})
            observation = Observation(**reset_data["observation"])
            done = bool(reset_data.get("done", False))
            max_ticks = int(observation.max_ticks)
        else:
            # Local evaluation: in-memory environment
            observation = env.reset()
            done = False
            max_ticks = int(env.max_ticks)
        
        final_metrics = {}
        
        # ========== Main Simulation Loop ==========
        for step in range(1, min(MAX_STEPS, max_ticks) + 1):
            if done:
                break
            
            # Query agent for action
            action = get_model_action(client, observation)
            action_repr = f"{action.action_type}('{action.target}')"
            
            # Execute action and receive feedback
            try:
                if CYBERSIM_ENV_URL:
                    # Remote: HTTP request
                    step_data = _http_json(
                        "POST",
                        f"{base}/step",
                        {
                            "action_type": action.action_type,
                            "target": action.target,
                            "metadata": action.metadata,
                        },
                    )
                    observation = Observation(**step_data["observation"])
                    reward_value = float(step_data["reward"]["value"])
                    done = bool(step_data.get("done", False))
                    info = step_data.get("info", {})
                    final_metrics = info.get("metrics", {})
                    success = bool(info.get("success", False))
                else:
                    # Local: in-process step
                    observation, reward, done, info = env.step(action)
                    reward_value = float(reward.value)
                    final_metrics = info.get("metrics", {})
                    success = bool(info.get("success", False))
                
                last_error = None
            
            except (Exception, urllib.error.URLError) as exc:
                # Step failed: timeout, network error, invalid action, etc.
                reward_value = 0.0
                done = True
                success = False
                last_error = str(exc)
            
            # Log step and accumulate data
            rewards.append(reward_value)
            steps_taken = step
            log_step(step=step, action=action_repr, reward=reward_value, done=done, error=last_error)
        
        # ========== Grading & Scoring ==========
        # DeterministicGrader evaluates agent performance on:
        # - Speed of detection (earlier = better)
        # - Accuracy of actions (correct > wrong > noop)
        # - Completion (success > incomplete)
        # Score is normalized to [0.0, 1.0]
        if final_metrics:
            score = grader.evaluate(final_metrics, success=success, max_ticks=max_ticks).score
            score = float(max(0.0, min(1.0, score)))  # Clamp to [0.0, 1.0]
        else:
            score = 0.0
    
    finally:
        # ========== Cleanup ==========
        # Always close environment, log final results
        try:
            if CYBERSIM_ENV_URL:
                _http_json("POST", f"{CYBERSIM_ENV_URL.rstrip('/')}/close", {})
            else:
                env.close()
        except Exception:
            # Silently ignore cleanup errors to preserve stdout contract
            pass
        
        # Final verdict: emit [END] log that judges parse
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    """
    Run the cybersecurity agent evaluation.
    
    This script is invoked by judges to test the agent:
        python inference.py
    
    It will:
    1. Load LLM credentials from environment (HF_TOKEN, API_BASE_URL, MODEL_NAME)
    2. Load the task scenario (CYBERSIM_TASK environment variable)
    3. Run the agent through the simulation for up to MAX_STEPS steps
    4. Grade the agent's performance
    5. Output results in [START]/[STEP]/[END] format to stdout
    
    For testing locally before submission:
        export API_BASE_URL="https://api.openai.com/v1"
        export MODEL_NAME="gpt-4o-mini"
        export HF_TOKEN="sk_..."  # Your API key
        python inference.py
    """
    main()


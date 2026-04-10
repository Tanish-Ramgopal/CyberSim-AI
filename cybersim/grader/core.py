from __future__ import annotations

from cybersim.grader import spec
from cybersim.models import EvaluationResult


class DeterministicGrader:
    """Episode grader: see `spec` and README.md ## Grader for the rubric."""

    def evaluate(self, metrics: dict, success: bool, max_ticks: int) -> EvaluationResult:
        score = 0.0
        reasoning = []
        difficulty = metrics.get("difficulty", spec.DEFAULT_DIFFICULTY)
        difficulty_bonus = spec.DIFFICULTY_BONUS.get(difficulty, 0.0)

        if metrics.get("attack_detected"):
            score += spec.WEIGHT_ATTACK_DETECTED
            reasoning.append(f"+{spec.WEIGHT_ATTACK_DETECTED} threat was detected")
        else:
            reasoning.append("+0.00 threat not detected")

        if success or metrics.get("mitigated"):
            score += spec.WEIGHT_MITIGATION
            reasoning.append(f"+{spec.WEIGHT_MITIGATION} mitigation action was correct")
        else:
            reasoning.append("+0.00 no successful mitigation")

        first_tick = metrics.get("first_response_tick")
        if first_tick is None:
            response_score = 0.0
        else:
            response_score = max(
                0.0,
                round(
                    spec.RESPONSE_SPEED_MAX - ((first_tick / max_ticks) * spec.RESPONSE_SPEED_MAX),
                    4,
                ),
            )
        score += response_score
        reasoning.append(f"+{response_score:.4f} response speed")

        score += difficulty_bonus
        reasoning.append(f"+{difficulty_bonus:.4f} difficulty calibration ({difficulty})")

        false_positives = int(metrics.get("false_positives", 0))
        wrong_actions = int(metrics.get("wrong_actions", 0))
        decoy_hits = int(metrics.get("decoy_hits", 0))
        stage_misses = int(metrics.get("stage_misses", 0))
        action_count = len(metrics.get("actions_taken", []))
        fp_penalty = min(spec.FP_CAP, false_positives * spec.FP_PER)
        wrong_penalty = min(spec.WRONG_CAP, wrong_actions * spec.WRONG_PER)
        decoy_penalty = min(spec.DECOY_CAP, decoy_hits * spec.DECOY_PER)
        stage_penalty = min(spec.STAGE_CAP, stage_misses * spec.STAGE_PER)
        chain_penalty = (
            spec.HARD_CHAIN_PENALTY
            if difficulty == "hard" and action_count < spec.HARD_CHAIN_MIN_ACTIONS
            else 0.0
        )
        score -= fp_penalty + wrong_penalty + decoy_penalty + stage_penalty + chain_penalty
        reasoning.append(f"-{fp_penalty:.4f} false positive penalty ({false_positives} invalid actions)")
        reasoning.append(f"-{wrong_penalty:.4f} wrong action penalty ({wrong_actions} wrong actions)")
        reasoning.append(f"-{decoy_penalty:.4f} decoy penalty ({decoy_hits} decoy actions)")
        reasoning.append(f"-{stage_penalty:.4f} stage dependency penalty ({stage_misses} misses)")
        reasoning.append(f"-{chain_penalty:.4f} hard-chain penalty ({action_count} actions)")

        bounded = max(spec.SCORE_MIN, min(spec.SCORE_MAX, round(score, 4)))
        status = "success" if success else "failed_goal"
        details = {
            "raw_score": score,
            "normalized_score": bounded,
            "success": success,
            "false_positives": false_positives,
            "wrong_actions": wrong_actions,
            "decoy_hits": decoy_hits,
            "stage_misses": stage_misses,
            "correct_actions": metrics.get("correct_actions", 0),
            "actions_taken": metrics.get("actions_taken", []),
        }
        return EvaluationResult(
            score=bounded,
            details=details,
            reasoning=reasoning,
            final_status=status,
            first_response_tick=first_tick,
        )

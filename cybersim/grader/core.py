from __future__ import annotations

from cybersim.models import EvaluationResult


class DeterministicGrader:
    def evaluate(self, metrics: dict, success: bool, max_ticks: int) -> EvaluationResult:
        score = 0.0
        reasoning = []
        difficulty = metrics.get("difficulty", "medium")
        difficulty_bonus = {"easy": 0.10, "medium": 0.03, "hard": 0.0}.get(difficulty, 0.0)

        if metrics.get("attack_detected"):
            score += 0.45
            reasoning.append("+0.45 threat was detected")
        else:
            reasoning.append("+0.00 threat not detected")

        if success or metrics.get("mitigated"):
            score += 0.25
            reasoning.append("+0.25 mitigation action was correct")
        else:
            reasoning.append("+0.00 no successful mitigation")

        first_tick = metrics.get("first_response_tick")
        if first_tick is None:
            response_score = 0.0
        else:
            response_score = max(0.0, round(0.15 - ((first_tick / max_ticks) * 0.15), 4))
        score += response_score
        reasoning.append(f"+{response_score:.4f} response speed")

        score += difficulty_bonus
        reasoning.append(f"+{difficulty_bonus:.4f} difficulty calibration ({difficulty})")

        false_positives = int(metrics.get("false_positives", 0))
        wrong_actions = int(metrics.get("wrong_actions", 0))
        decoy_hits = int(metrics.get("decoy_hits", 0))
        stage_misses = int(metrics.get("stage_misses", 0))
        action_count = len(metrics.get("actions_taken", []))
        fp_penalty = min(0.40, false_positives * 0.12)
        wrong_penalty = min(0.40, wrong_actions * 0.12)
        decoy_penalty = min(0.30, decoy_hits * 0.15)
        stage_penalty = min(0.30, stage_misses * 0.15)
        chain_penalty = 0.18 if difficulty == "hard" and action_count < 3 else 0.0
        score -= fp_penalty + wrong_penalty + decoy_penalty + stage_penalty + chain_penalty
        reasoning.append(f"-{fp_penalty:.4f} false positive penalty ({false_positives} invalid actions)")
        reasoning.append(f"-{wrong_penalty:.4f} wrong action penalty ({wrong_actions} wrong actions)")
        reasoning.append(f"-{decoy_penalty:.4f} decoy penalty ({decoy_hits} decoy actions)")
        reasoning.append(f"-{stage_penalty:.4f} stage dependency penalty ({stage_misses} misses)")
        reasoning.append(f"-{chain_penalty:.4f} hard-chain penalty ({action_count} actions)")

        bounded = max(0.0, min(1.0, round(score, 4)))
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


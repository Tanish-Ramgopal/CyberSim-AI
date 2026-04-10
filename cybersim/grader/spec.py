"""
Canonical numeric rubric for `DeterministicGrader`.

Keep in sync with README.md (## Grader) and `cybersim/grader/core.py`.
All grader math should use these constants so docs cannot drift from code.
"""

from __future__ import annotations

from typing import Final

# Final episode score is clamped to this inclusive range.
SCORE_MIN: Final[float] = 0.0
SCORE_MAX: Final[float] = 1.0

# Additive terms (before penalties)
WEIGHT_ATTACK_DETECTED: Final[float] = 0.45
WEIGHT_MITIGATION: Final[float] = 0.25
# Response speed: max(0, RESPONSE_SPEED_MAX - (first_tick / max_ticks) * RESPONSE_SPEED_MAX)
RESPONSE_SPEED_MAX: Final[float] = 0.15

DIFFICULTY_BONUS: Final[dict[str, float]] = {
    "easy": 0.10,
    "medium": 0.03,
    "hard": 0.0,
}
DEFAULT_DIFFICULTY: Final[str] = "medium"

# Penalties (per unit / caps)
FP_PER: Final[float] = 0.12
FP_CAP: Final[float] = 0.40
WRONG_PER: Final[float] = 0.12
WRONG_CAP: Final[float] = 0.40
DECOY_PER: Final[float] = 0.15
DECOY_CAP: Final[float] = 0.30
STAGE_PER: Final[float] = 0.15
STAGE_CAP: Final[float] = 0.30
HARD_CHAIN_PENALTY: Final[float] = 0.18
HARD_CHAIN_MIN_ACTIONS: Final[int] = 3

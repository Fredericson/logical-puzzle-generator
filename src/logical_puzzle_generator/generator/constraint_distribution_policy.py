from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.generator.difficulty import Difficulty, DifficultyPolicy


RELATION_TYPES = (
    DirectLeftOfConstraint,
    LeftOfConstraint,
    DirectRightOfConstraint,
    RightOfConstraint,
    AdjacentConstraint,
)
SUPPORTED_TYPES = (FixedPositionConstraint, *RELATION_TYPES)


@dataclass(frozen=True, slots=True)
class ConstraintDistribution:
    """Deterministic analysis result for a constraint type distribution."""

    score: int
    counts: Counter[type[Constraint]]
    unique_relation_types: int
    dominant_count: int
    relation_count: int


class ConstraintDistributionPolicy:
    """
    Scores and filters generated constraint distributions for clue variety.

    The policy is a quality optimization only. It does not solve puzzles,
    generate solutions, validate uniqueness, render clues, or translate text.
    """

    _UNIQUE_RELATION_WEIGHT = 24
    _RELATION_COUNT_WEIGHT = 2
    _DIRECTIONAL_BONUS = 8
    _ADJACENT_BONUS = 5
    _DIRECT_BONUS = 5
    _FIXED_MATCH_BONUS = 12
    _DUPLICATE_PENALTY = 8
    _DOMINANCE_PENALTY = 10
    _OVERUSE_PENALTY = 9
    _OPPOSITE_PAIR_BONUS = 4

    def analyze(self, constraints: Iterable[Constraint]) -> ConstraintDistribution:
        items = list(constraints)
        counts: Counter[type[Constraint]] = Counter(type(constraint) for constraint in items)
        relation_counts = Counter(
            constraint_type for constraint_type, count in counts.items()
            if constraint_type in RELATION_TYPES for _ in range(count)
        )
        relation_count = sum(relation_counts.values())
        unique_relation_types = len(relation_counts)
        dominant_count = max(relation_counts.values(), default=0)
        duplicate_count = sum(count - 1 for count in relation_counts.values() if count > 1)
        overuse_count = sum(max(0, count - 2) for count in relation_counts.values())

        score = (
            unique_relation_types * self._UNIQUE_RELATION_WEIGHT
            + relation_count * self._RELATION_COUNT_WEIGHT
            - duplicate_count * self._DUPLICATE_PENALTY
            - max(0, dominant_count - 1) * self._DOMINANCE_PENALTY
            - overuse_count * self._OVERUSE_PENALTY
        )

        if counts[FixedPositionConstraint] == 0:
            score += self._FIXED_MATCH_BONUS
        if relation_counts[AdjacentConstraint]:
            score += self._ADJACENT_BONUS
        if relation_counts[DirectLeftOfConstraint] or relation_counts[DirectRightOfConstraint]:
            score += self._DIRECT_BONUS
        if any(relation_counts[constraint_type] for constraint_type in RELATION_TYPES):
            score += self._DIRECTIONAL_BONUS
        if relation_counts[LeftOfConstraint] and relation_counts[RightOfConstraint]:
            score += self._OPPOSITE_PAIR_BONUS
        if relation_counts[DirectLeftOfConstraint] and relation_counts[DirectRightOfConstraint]:
            score += self._OPPOSITE_PAIR_BONUS

        return ConstraintDistribution(
            score=score,
            counts=counts,
            unique_relation_types=unique_relation_types,
            dominant_count=dominant_count,
            relation_count=relation_count,
        )

    def score(self, constraints: Iterable[Constraint]) -> int:
        return self.analyze(constraints).score

    def accepts(self, constraints: Iterable[Constraint], difficulty: Difficulty | str | None = None) -> bool:
        items = list(constraints)
        analysis = self.analyze(items)
        if analysis.relation_count <= 1:
            return True

        normalized = DifficultyPolicy().normalize(difficulty)
        fixed_count = analysis.counts[FixedPositionConstraint]
        if normalized is Difficulty.EASY and fixed_count != 2:
            return False
        if normalized is Difficulty.MEDIUM and fixed_count != 1:
            return False
        if normalized is Difficulty.HARD and fixed_count != 0:
            return False

        if analysis.unique_relation_types < 2 and analysis.relation_count >= 3:
            return False
        if analysis.dominant_count > max(2, analysis.relation_count - 1):
            return False
        if normalized is Difficulty.HARD and analysis.relation_count >= 3:
            left_right = analysis.counts[LeftOfConstraint] + analysis.counts[RightOfConstraint]
            if left_right >= analysis.relation_count - 1:
                return False
        return True

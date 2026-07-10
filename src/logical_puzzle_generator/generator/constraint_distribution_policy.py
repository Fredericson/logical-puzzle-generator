from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint

RelationScore = tuple[int, int, int, int, int]

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

    score: RelationScore
    counts: Counter[type[Constraint]]
    relation_counts: Counter[type[Constraint]]
    unique_relation_types: int
    duplicate_relation_count: int
    dominant_relation_count: int
    relation_count: int


class ConstraintDistributionPolicy:
    """
    Scores and filters generated constraint distributions for clue variety.

    The policy receives only neutral distribution context. It does not know
    about level names, solve puzzles, generate solutions, validate
    uniqueness, render clues, or translate text.
    """

    def analyze(self, constraints: Iterable[Constraint]) -> ConstraintDistribution:
        counts: Counter[type[Constraint]] = Counter(type(constraint) for constraint in constraints)
        relation_counts: Counter[type[Constraint]] = Counter(
            {
                constraint_type: count
                for constraint_type, count in counts.items()
                if constraint_type in RELATION_TYPES
            }
        )
        relation_count = sum(relation_counts.values())
        unique_relation_types = len(relation_counts)
        duplicate_relation_count = sum(count - 1 for count in relation_counts.values() if count > 1)
        dominant_relation_count = max(relation_counts.values(), default=0)
        has_adjacent = int(relation_counts[AdjacentConstraint] > 0)
        has_direct_relation = int(
            relation_counts[DirectLeftOfConstraint] > 0
            or relation_counts[DirectRightOfConstraint] > 0
        )

        return ConstraintDistribution(
            score=(
                unique_relation_types,
                -duplicate_relation_count,
                -dominant_relation_count,
                has_adjacent,
                has_direct_relation,
            ),
            counts=counts,
            relation_counts=relation_counts,
            unique_relation_types=unique_relation_types,
            duplicate_relation_count=duplicate_relation_count,
            dominant_relation_count=dominant_relation_count,
            relation_count=relation_count,
        )

    def score(self, constraints: Iterable[Constraint]) -> RelationScore:
        return self.analyze(constraints).score

    def accepts(
        self,
        constraints: Iterable[Constraint],
        *,
        required_fixed_count: int | None = None,
        item_count: int | None = None,
    ) -> bool:
        analysis = self.analyze(constraints)

        if (
            required_fixed_count is not None
            and analysis.counts[FixedPositionConstraint] != required_fixed_count
        ):
            return False

        if analysis.relation_count <= 2:
            return True

        if item_count is not None and item_count != 4:
            return True

        if analysis.unique_relation_types < 2:
            return False

        if analysis.dominant_relation_count > 2:
            return False

        ordinary_left_right_count = (
            analysis.relation_counts[LeftOfConstraint]
            + analysis.relation_counts[RightOfConstraint]
        )
        if ordinary_left_right_count == analysis.relation_count:
            return False

        return True

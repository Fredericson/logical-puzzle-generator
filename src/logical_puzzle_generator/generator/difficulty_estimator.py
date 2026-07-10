from __future__ import annotations

from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.model.puzzle import Puzzle


class DifficultyEstimator:
    """
    Estimates child-facing puzzle difficulty from final visible constraints.

    The estimator intentionally uses only constraint semantics from the clue set
    that remains after reduction. It does not inspect removed constraints,
    rendered clue wording, PDF localisation, or the target solution as a
    shortcut.
    """

    EASY = 1
    MEDIUM = 2
    HARD = 3

    def estimate(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        constraints = self._constraints_from(puzzle_or_constraints)
        if not constraints:
            return self.HARD

        anchor_count = sum(isinstance(c, FixedPositionConstraint) for c in constraints)
        strong_count = sum(
            isinstance(c, DirectLeftOfConstraint | DirectRightOfConstraint) for c in constraints
        )
        adjacent_count = sum(isinstance(c, AdjacentConstraint) for c in constraints)
        weak_count = sum(isinstance(c, LeftOfConstraint | RightOfConstraint) for c in constraints)

        score = 0
        if anchor_count:
            score -= 1
        else:
            score += 2

        score -= strong_count
        score += adjacent_count
        score += weak_count * 2

        if weak_count >= 2:
            score += 1

        ambiguous_count = adjacent_count + weak_count
        if anchor_count and ambiguous_count >= 3 and ambiguous_count > strong_count:
            score += 1

        if not anchor_count and strong_count == 0 and ambiguous_count >= 2:
            score += 1

        if score <= 0:
            return self.EASY
        if not anchor_count and strong_count == 0 and adjacent_count >= 3:
            return self.HARD
        if score <= 6:
            return self.MEDIUM
        return self.HARD

    def _constraints_from(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> list[Constraint]:
        if isinstance(puzzle_or_constraints, Puzzle):
            return list(puzzle_or_constraints.constraints)
        return list(puzzle_or_constraints)

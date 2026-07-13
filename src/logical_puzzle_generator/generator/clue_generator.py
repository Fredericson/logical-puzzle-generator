from __future__ import annotations

from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType


class ClueGenerator:
    """
    Converts existing mathematical constraints into human-readable clues.

    Commit 10.3 intentionally does not create constraints, solve puzzles,
    validate uniqueness, optimize difficulty, or randomize output. Each clue
    produced by this generator corresponds to exactly one supplied constraint.
    """

    def __init__(self, item_count: int | None = None) -> None:
        self._item_count = item_count

    def generate(
        self,
        constraints: Iterable[Constraint],
    ) -> list[Clue]:
        """
        Generate deterministic clues for an iterable of constraints.
        """
        unique_clues: list[Clue] = []
        seen: set[tuple[ClueType, str]] = set()

        for constraint in constraints:
            if not isinstance(constraint, Constraint):
                raise TypeError("ClueGenerator requires Constraint instances.")

            clue = self._clue_from_constraint(constraint)
            clue_key = (clue.clue_type, clue.text)

            if clue_key not in seen:
                unique_clues.append(clue)
                seen.add(clue_key)

        return unique_clues

    def _clue_from_constraint(
        self,
        constraint: Constraint,
    ) -> Clue:
        if isinstance(constraint, FixedPositionConstraint):
            return Clue(
                clue_type=ClueType.FIXED_POSITION,
                text=self._sentence(self._fixed_position_description(constraint)),
                constraint=constraint,
            )

        if isinstance(constraint, LeftOfConstraint):
            return Clue(
                clue_type=ClueType.LEFT_OF,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        if isinstance(constraint, RightOfConstraint):
            return Clue(
                clue_type=ClueType.RIGHT_OF,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        if isinstance(constraint, DirectLeftOfConstraint):
            return Clue(
                clue_type=ClueType.DIRECT_LEFT_OF,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        if isinstance(constraint, DirectRightOfConstraint):
            return Clue(
                clue_type=ClueType.DIRECT_RIGHT_OF,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        if isinstance(constraint, AdjacentConstraint):
            return Clue(
                clue_type=ClueType.ADJACENT,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        if isinstance(constraint, SamePositionConstraint):
            return Clue(
                clue_type=ClueType.SAME_POSITION,
                text=self._sentence(constraint.description),
                constraint=constraint,
            )

        raise TypeError(f"Unsupported constraint type: {constraint.__class__.__name__}.")

    def _sentence(self, text: str) -> str:
        if text.endswith("."):
            return text

        return f"{text}."

    def _fixed_position_description(self, constraint: FixedPositionConstraint) -> str:
        if constraint.position.index == 1:
            return f"{constraint.item} stands at the far left"

        if self._item_count is not None and constraint.position.index == self._item_count:
            return f"{constraint.item} stands at the far right"

        return constraint.description

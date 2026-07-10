from __future__ import annotations

from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType


class ClueGenerator:
    """
    Converts existing mathematical constraints into human-readable clues.

    Commit 10.3 intentionally does not create constraints, solve puzzles,
    validate uniqueness, optimize difficulty, or randomize output. Each clue
    produced by this generator corresponds to exactly one supplied constraint.
    """

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
                text=self._sentence(constraint.description),
            )

        if isinstance(constraint, LeftOfConstraint):
            return Clue(
                clue_type=ClueType.LEFT_OF,
                text=self._sentence(constraint.description),
            )

        if isinstance(constraint, RightOfConstraint):
            return Clue(
                clue_type=ClueType.RIGHT_OF,
                text=self._sentence(constraint.description),
            )

        if isinstance(constraint, AdjacentConstraint):
            return Clue(
                clue_type=ClueType.ADJACENT,
                text=self._sentence(constraint.description),
            )

        raise TypeError(
            f"Unsupported constraint type: {constraint.__class__.__name__}."
        )

    def _sentence(self, text: str) -> str:
        if text.endswith("."):
            return text

        return f"{text}."

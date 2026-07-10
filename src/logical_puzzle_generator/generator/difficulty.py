from __future__ import annotations

from collections.abc import Iterable
from enum import Enum

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.model.puzzle import Puzzle


class Difficulty(Enum):
    """Selectable Version 1 puzzle difficulty."""

    EASY = ("easy", 1)
    MEDIUM = ("medium", 2)
    HARD = ("hard", 3)

    def __init__(self, cli_value: str, metadata_value: int) -> None:
        self.cli_value = cli_value
        self.metadata_value = metadata_value


class DifficultyPolicy:
    """Classify final visible constraints by fixed-position clue count only."""

    def normalize(self, difficulty: Difficulty | str | None) -> Difficulty | None:
        if difficulty is None:
            return None
        if isinstance(difficulty, Difficulty):
            return difficulty
        if isinstance(difficulty, str):
            normalized = difficulty.strip().lower()
            for candidate in Difficulty:
                if candidate.cli_value == normalized:
                    return candidate
        allowed = ", ".join(d.cli_value for d in Difficulty)
        raise ValueError(f"Unsupported difficulty {difficulty!r}. Expected one of: {allowed}.")

    def classify(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> Difficulty:
        count = self.fixed_position_count(puzzle_or_constraints)
        if count == 2:
            return Difficulty.EASY
        if count == 1:
            return Difficulty.MEDIUM
        if count == 0:
            return Difficulty.HARD
        raise ValueError(
            f"Invalid Version 1 fixed-position clue count {count}. "
            "Expected exactly 2, 1, or 0."
        )

    def metadata_value(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        return self.classify(puzzle_or_constraints).metadata_value

    def estimate(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        return self.metadata_value(puzzle_or_constraints)

    def matches(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        difficulty: Difficulty | str,
    ) -> bool:
        try:
            return self.classify(puzzle_or_constraints) is self.normalize(difficulty)
        except ValueError:
            return False

    def fixed_position_count(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        constraints = (
            puzzle_or_constraints.constraints
            if isinstance(puzzle_or_constraints, Puzzle)
            else puzzle_or_constraints
        )
        return sum(isinstance(constraint, FixedPositionConstraint) for constraint in constraints)

    def required_fixed_position_count(self, difficulty: Difficulty | str) -> int:
        requested = self.normalize(difficulty)
        if requested is Difficulty.EASY:
            return 2
        if requested is Difficulty.MEDIUM:
            return 1
        if requested is Difficulty.HARD:
            return 0
        raise ValueError("A concrete difficulty is required.")

    def can_remove_to_match(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        difficulty: Difficulty | str,
    ) -> bool:
        count = self.fixed_position_count(puzzle_or_constraints)
        try:
            return count == self.required_fixed_position_count(difficulty)
        except ValueError:
            return False

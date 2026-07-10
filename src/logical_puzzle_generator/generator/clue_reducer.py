from __future__ import annotations

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.puzzle import Puzzle


class ClueReducer:
    """
    Removes unnecessary visible clues while preserving a uniquely solvable puzzle.

    Every visible clue owns exactly one mathematical constraint. Candidate
    puzzles are validated only with constraints for their remaining visible
    clues, so no hidden constraints can influence uniqueness.
    """

    def __init__(
        self,
        validator: Validator | None = None,
    ) -> None:
        self._validator = validator if validator is not None else Validator()

    def reduce(
        self,
        puzzle: Puzzle,
    ) -> Puzzle:
        """
        Return a puzzle reduced by the deterministic remove-and-validate pass.
        """
        self._validate_puzzle(puzzle)

        reduced = self._copy_with_clues(puzzle, list(puzzle.clues))
        changed = True

        while changed:
            changed = False

            if len(reduced.clues) <= 1:
                break

            for index in range(len(reduced.clues)):
                candidate_clues = [
                    clue for clue_index, clue in enumerate(reduced.clues) if clue_index != index
                ]
                candidate = self._copy_with_clues(reduced, candidate_clues)

                if self._would_remove_required_variation(reduced, candidate):
                    continue

                if self._validator.has_unique_solution(candidate):
                    reduced = candidate
                    changed = True
                    break

        return reduced

    def _validate_puzzle(
        self,
        puzzle: Puzzle,
    ) -> None:
        if not isinstance(puzzle, Puzzle):
            raise TypeError("ClueReducer requires a Puzzle instance.")

        if any(not isinstance(clue, Clue) for clue in puzzle.clues):
            raise TypeError("ClueReducer requires puzzle clues to be Clue instances.")

        if len(puzzle.clues) != len(puzzle.constraints):
            raise ValueError("ClueReducer requires matching clue and constraint counts.")

        for clue, constraint in zip(puzzle.clues, puzzle.constraints, strict=True):
            if not isinstance(clue.constraint, Constraint):
                raise TypeError("ClueReducer requires every clue to reference a Constraint.")
            if clue.constraint is not constraint:
                raise ValueError(
                    "ClueReducer requires each clue to correspond to the constraint "
                    "at the same index."
                )

    def _copy_with_clues(
        self,
        puzzle: Puzzle,
        clues: list[Clue],
    ) -> Puzzle:
        return Puzzle(
            items=puzzle.items,
            constraints=[clue.constraint for clue in clues],
            clues=clues,
            metadata=puzzle.metadata,
            solution=puzzle.solution,
        )

    def _would_remove_required_variation(
        self,
        current: Puzzle,
        candidate: Puzzle,
    ) -> bool:
        if len(current.items) != 4:
            return False

        current_meanings = self._clue_meanings(current.clues)
        if len(current_meanings) < 2:
            return False

        return len(self._clue_meanings(candidate.clues)) < 2

    def _clue_meanings(self, clues: list[Clue]) -> set[str]:
        return {self._clue_meaning(clue) for clue in clues}

    def _clue_meaning(self, clue: Clue) -> str:
        constraint = clue.constraint

        if isinstance(constraint, FixedPositionConstraint):
            if constraint.position.index == 1:
                return "far_left"
            return "far_right"

        if isinstance(constraint, DirectLeftOfConstraint):
            return "directly_left_of"

        if isinstance(constraint, LeftOfConstraint):
            return "left_of"

        if isinstance(constraint, DirectRightOfConstraint):
            return "directly_right_of"

        if isinstance(constraint, RightOfConstraint):
            return "right_of"

        if isinstance(constraint, AdjacentConstraint):
            return "next_to"

        return clue.clue_type.value

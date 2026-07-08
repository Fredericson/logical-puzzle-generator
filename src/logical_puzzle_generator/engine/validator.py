from __future__ import annotations

from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.model.puzzle import Puzzle


class Validator:
    """
    Validates logical puzzles using the solver.
    """

    def __init__(self) -> None:
        self._solver = Solver()

    def has_unique_solution(
        self,
        puzzle: Puzzle,
    ) -> bool:
        """
        Returns True if the puzzle has exactly one solution.
        """

        result = self._solver.solve(
            puzzle,
            stop_after=2,
        )

        return result.has_unique_solution

    def is_valid(
        self,
        puzzle: Puzzle,
    ) -> bool:
        """
        Returns True if the puzzle has at least one solution.
        """

        result = self._solver.solve(puzzle)

        return result.has_solution

# Replace the entire file with this version.

from __future__ import annotations

import time

from logical_puzzle_generator.engine.assignment_iterator import (
    AssignmentIterator,
)
from logical_puzzle_generator.engine.solver_result import SolverResult
from logical_puzzle_generator.engine.statistics import SolverStatistics
from logical_puzzle_generator.model.puzzle import Puzzle


class Solver:
    """
    Simple brute force solver for 4x4 logical puzzles.

    The solver enumerates all possible assignments and keeps
    those satisfying every constraint.
    """

    def __init__(self) -> None:
        self._iterator = AssignmentIterator()

    def solve(
        self,
        puzzle: Puzzle,
        stop_after: int | None = None,
    ) -> SolverResult:
        """
        Solve the given puzzle.

        Parameters
        ----------
        puzzle:
            Puzzle to solve.

        stop_after:
            Stop after the given number of solutions have been
            found. Useful for uniqueness checks.
        """

        start = time.perf_counter()

        result = SolverResult()
        stats = SolverStatistics()

        for assignment in self._iterator.iterate(
            puzzle.items
        ):

            stats.assignments_checked += 1

            valid = all(
                constraint.matches(assignment)
                for constraint in puzzle.constraints
            )

            if not valid:
                continue

            stats.valid_assignments += 1
            result.solutions.append(assignment)

            if (
                stop_after is not None
                and result.solution_count >= stop_after
            ):
                break

        stats.elapsed_time_ms = (
            time.perf_counter() - start
        ) * 1000

        result.statistics = stats

        return result

from __future__ import annotations

import time

from logical_puzzle_generator.engine.assignment_iterator import (
    AssignmentIterator,
)
from logical_puzzle_generator.engine.solver_result import SolverResult
from logical_puzzle_generator.engine.statistics import SolverStatistics


class Solver:
    """
    Simple brute force solver for 4x4 puzzles.
    """

    def __init__(self) -> None:

        self._iterator = AssignmentIterator()

    from logical_puzzle_generator.model.puzzle import Puzzle

    def solve(
        self,
        puzzle: Puzzle,
    ) -> SolverResult:
        start = time.perf_counter()

        result = SolverResult()

        stats = SolverStatistics()

        for assignment in self._iterator.iterate(
            puzzle.items
        ):

            stats.assignments_checked += 1

            valid = True

            for constraint in puzzle.constraints:

                if not constraint.matches(assignment):

                    valid = False
                    break

            if valid:

                stats.valid_assignments += 1

                result.solutions.append(assignment)

        result.statistics = stats
        result.statistics.elapsed_time_ms = (
            time.perf_counter() - start
        ) * 1000

        return result

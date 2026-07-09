from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.engine.assignment import Assignment


@dataclass(slots=True)
class Solution:
    """
    Represents the final solution of a logical puzzle.

    For version 1.0 a solution consists of exactly one
    assignment mapping every player to a position.

    Additional category assignments (shirt colour, racket,
    drink, ...) will be derived from this solution by the
    puzzle generator and therefore do not belong into this
    class.
    """

    assignment: Assignment

    solver_iterations: int = 0

    @property
    def positions(self):
        return self.assignment.positions

    @property
    def player_count(self) -> int:
        """
        Number of players contained in the solution.
        """
        return len(self.assignment)

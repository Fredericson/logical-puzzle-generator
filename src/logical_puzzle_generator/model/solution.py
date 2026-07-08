from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.engine.assignment import Assignment


@dataclass(slots=True)
class Solution:
    """
    Final solution of a puzzle.
    """

    assignment: Assignment

    solver_iterations: int = 0

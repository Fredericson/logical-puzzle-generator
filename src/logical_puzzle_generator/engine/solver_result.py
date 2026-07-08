from __future__ import annotations

from dataclasses import dataclass, field

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.engine.statistics import SolverStatistics


@dataclass(slots=True)
class SolverResult:
    """
    Result returned by the solver.
    """

    solutions: list[Assignment] = field(default_factory=list)

    statistics: SolverStatistics = field(
        default_factory=SolverStatistics
    )

    @property
    def solution_count(self) -> int:
        return len(self.solutions)

    @property
    def has_solution(self) -> bool:
        return self.solution_count > 0

    @property
    def has_unique_solution(self) -> bool:
        return self.solution_count == 1

    @property
    def first_solution(self) -> Assignment | None:
        if not self.solutions:
            return None
        return self.solutions[0]

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SolverStatistics:
    """
    Runtime statistics collected while solving one puzzle.
    """

    assignments_checked: int = 0

    valid_assignments: int = 0

    elapsed_time_ms: float = 0.0

    @property
    def rejected_assignments(self) -> int:
        return self.assignments_checked - self.valid_assignments

from __future__ import annotations

from logical_puzzle_generator.engine.assignment import Assignment


class AssignmentBuilder:

    def __init__(self) -> None:
        self._assignments: list[Assignment] = []

    def add(self, assignment: Assignment) -> None:
        self._assignments.append(assignment)

    def build(self) -> list[Assignment]:
        return list(self._assignments)

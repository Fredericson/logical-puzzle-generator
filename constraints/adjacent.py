from .base import Constraint

class AdjacentConstraint(Constraint):
    def __init__(self, first: str, second: str):
        self.first = first
        self.second = second

    def matches(self, assignment):
        return abs(
            assignment.position_of(self.first) -
            assignment.position_of(self.second)
        ) == 1

    @property
    def description(self):
        return f"{self.first} stands next to {self.second}"

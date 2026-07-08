from .base import Constraint

class FixedPositionConstraint(Constraint):
    def __init__(self, item: str, position: int):
        self.item = item
        self.position = position

    def matches(self, assignment):
        return assignment.position_of(self.item) == self.position

    @property
    def description(self):
        return f"{self.item} stands at position {self.position}"

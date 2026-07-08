from .base import Constraint

class LeftOfConstraint(Constraint):
    def __init__(self, left: str, right: str):
        self.left = left
        self.right = right

    def matches(self, assignment):
        return assignment.position_of(self.left) < assignment.position_of(self.right)

    @property
    def description(self):
        return f"{self.left} stands left of {self.right}"

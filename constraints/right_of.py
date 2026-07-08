from .base import Constraint

class RightOfConstraint(Constraint):
    def __init__(self, right: str, left: str):
        self.right = right
        self.left = left

    def matches(self, assignment):
        return assignment.position_of(self.right) > assignment.position_of(self.left)

    @property
    def description(self):
        return f"{self.right} stands right of {self.left}"

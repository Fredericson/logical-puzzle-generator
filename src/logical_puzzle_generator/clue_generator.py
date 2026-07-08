from __future__ import annotations

from .assignment import Assignment
from .constraint_engine import (
    FixedPositionConstraint,
    LeftOfConstraint,
    AdjacentConstraint,
)

class ClueGenerator:
    def generate(self, assignment: Assignment):
        clues=[]
        items=list(assignment.positions.keys())

        for item,pos in assignment.positions.items():
            clues.append(FixedPositionConstraint(item,pos))

        for i,left in enumerate(items):
            for right in items[i+1:]:
                if assignment.position_of(left)<assignment.position_of(right):
                    clues.append(LeftOfConstraint(left,right))

        for i,a in enumerate(items):
            for b in items[i+1:]:
                if abs(assignment.position_of(a)-assignment.position_of(b))==1:
                    clues.append(AdjacentConstraint(a,b))

        return clues

from __future__ import annotations

from abc import ABC, abstractmethod
from .assignment import Assignment

class Constraint(ABC):
    @abstractmethod
    def matches(self, assignment: Assignment) -> bool:
        ...

class FixedPositionConstraint(Constraint):
    def __init__(self,item:str,position:int):
        self.item=item
        self.position=position

    def matches(self, assignment: Assignment)->bool:
        return assignment.position_of(self.item)==self.position

class LeftOfConstraint(Constraint):
    def __init__(self,left:str,right:str):
        self.left=left
        self.right=right

    def matches(self, assignment: Assignment)->bool:
        return assignment.position_of(self.left)<assignment.position_of(self.right)

class AdjacentConstraint(Constraint):
    def __init__(self,a:str,b:str):
        self.a=a
        self.b=b

    def matches(self, assignment: Assignment)->bool:
        return abs(assignment.position_of(self.a)-assignment.position_of(self.b))==1

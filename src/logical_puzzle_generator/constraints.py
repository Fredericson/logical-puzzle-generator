from abc import ABC, abstractmethod
from .assignment import Assignment
class Constraint(ABC):
    @abstractmethod
    def matches(self,a:Assignment)->bool: ...
class FixedPosition(Constraint):
    def __init__(self,item,pos): self.item=item; self.pos=pos
    def matches(self,a): return a.position_of(self.item)==self.pos
class LeftOf(Constraint):
    def __init__(self,l,r): self.l=l; self.r=r
    def matches(self,a): return a.position_of(self.l)<a.position_of(self.r)
class Adjacent(Constraint):
    def __init__(self,a1,a2): self.a1=a1; self.a2=a2
    def matches(self,a): return abs(a.position_of(self.a1)-a.position_of(self.a2))==1

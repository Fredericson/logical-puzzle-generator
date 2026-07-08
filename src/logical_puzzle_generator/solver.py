from itertools import permutations
from .assignment import Assignment
class Solver:
    def solve(self,items,constraints):
        out=[]
        for p in permutations(range(1,len(items)+1)):
            a=Assignment(dict(zip(items,p)))
            if all(c.matches(a) for c in constraints):
                out.append(a)
        return out
    def count(self,items,constraints):
        return len(self.solve(items,constraints))

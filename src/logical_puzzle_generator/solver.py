from itertools import permutations
from .assignment import Assignment

class Solver:
    def solve(self, items, constraints):
        solutions=[]
        for perm in permutations(range(1,len(items)+1)):
            assignment=Assignment(dict(zip(items,perm)))
            if all(c.matches(assignment) for c in constraints):
                solutions.append(assignment)
        return solutions

    def count(self, items,constraints):
        return len(self.solve(items,constraints))

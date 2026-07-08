from __future__ import annotations

from .solver import Solver

class Validator:
    def __init__(self):
        self.solver = Solver()

    def has_unique_solution(self, items, constraints)->bool:
        return self.solver.count_solutions(items,constraints)==1

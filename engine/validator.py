class Validator:
    def __init__(self, solver):
        self.solver=solver

    def has_unique_solution(self, items, constraints):
        return self.solver.count(items,constraints)==1

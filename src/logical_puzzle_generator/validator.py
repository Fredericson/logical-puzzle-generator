from .solver import Solver
class Validator:
    def __init__(self): self.solver=Solver()
    def unique(self,items,constraints):
        return self.solver.count(items,constraints)==1

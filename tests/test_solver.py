from logical_puzzle_generator.solver import Solver
from logical_puzzle_generator.constraints import fixed_position

def test_fixed_position():
    solver = Solver()
    items = ["A","B","C","D"]
    count = solver.count_solutions(items,[fixed_position("A",1)])
    assert count == 6

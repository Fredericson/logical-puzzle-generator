from logical_puzzle_generator.solver import Solver
from logical_puzzle_generator.constraints import FixedPosition
def test_count():
    assert Solver().count(['A','B','C','D'],[FixedPosition('A',1)])==6

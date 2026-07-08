from logical_puzzle_generator.validator import Validator
from logical_puzzle_generator.constraints import FixedPosition
def test_unique_false():
    assert not Validator().unique(['A','B','C','D'],[FixedPosition('A',1)])

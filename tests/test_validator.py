from logical_puzzle_generator.validator import Validator
from logical_puzzle_generator.constraints import fixed_position

def test_not_unique():
    v=Validator()
    assert not v.has_unique_solution(
        ["A","B","C","D"],
        [fixed_position("A",1)]
    )

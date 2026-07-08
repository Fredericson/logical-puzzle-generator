from logical_puzzle_generator.assignment import Assignment
from logical_puzzle_generator.constraint_engine import (
    FixedPositionConstraint,
    LeftOfConstraint,
    AdjacentConstraint,
)

def test_constraints():
    a=Assignment({"A":1,"B":2,"C":3,"D":4})
    assert FixedPositionConstraint("A",1).matches(a)
    assert LeftOfConstraint("A","D").matches(a)
    assert AdjacentConstraint("B","C").matches(a)

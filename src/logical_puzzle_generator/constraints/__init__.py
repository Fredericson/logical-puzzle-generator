from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint

FixedPosition = FixedPositionConstraint
LeftOf = LeftOfConstraint
Adjacent = AdjacentConstraint
RightOf = RightOfConstraint

__all__ = [
    "Adjacent",
    "AdjacentConstraint",
    "Constraint",
    "FixedPosition",
    "FixedPositionConstraint",
    "LeftOf",
    "LeftOfConstraint",
    "RightOf",
    "RightOfConstraint",
]

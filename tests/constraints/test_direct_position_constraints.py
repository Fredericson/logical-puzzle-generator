from logical_puzzle_generator.constraints import DirectLeftOfConstraint, DirectRightOfConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


def test_direct_left_of_matches_only_adjacent_positions() -> None:
    emma = Item("Emma")
    aurelia = Item("Aurelia")
    assignment = Assignment({emma: Position(1), aurelia: Position(2)})
    non_adjacent = Assignment({emma: Position(1), aurelia: Position(3)})

    constraint = DirectLeftOfConstraint(emma, aurelia)

    assert constraint.matches(assignment)
    assert not constraint.matches(non_adjacent)
    assert constraint.description == "Emma stands directly left of Aurelia"


def test_direct_right_of_matches_only_adjacent_positions() -> None:
    emma = Item("Emma")
    aurelia = Item("Aurelia")
    assignment = Assignment({emma: Position(1), aurelia: Position(2)})
    non_adjacent = Assignment({emma: Position(1), aurelia: Position(3)})

    constraint = DirectRightOfConstraint(aurelia, emma)

    assert constraint.matches(assignment)
    assert not constraint.matches(non_adjacent)
    assert constraint.description == "Aurelia stands directly right of Emma"

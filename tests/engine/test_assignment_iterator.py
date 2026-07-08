from logical_puzzle_generator.engine.assignment_iterator import (
    AssignmentIterator,
)
from logical_puzzle_generator.model.item import Item


def test_iterator():

    iterator = AssignmentIterator()

    items = [
        Item("A"),
        Item("B"),
        Item("C"),
        Item("D"),
    ]

    assignments = list(iterator.iterate(items))

    assert len(assignments) == 24

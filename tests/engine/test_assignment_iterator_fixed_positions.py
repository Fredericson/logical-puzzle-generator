from __future__ import annotations

import pytest

from logical_puzzle_generator.engine.assignment_iterator import AssignmentIterator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


def _children() -> list[Item]:
    return [Item("A"), Item("B"), Item("C"), Item("D")]


def _values() -> list[Item]:
    return [Item(f"v{i}", category_id="theme") for i in range(4)]


def test_position_only_assignment_iterator_generates_24_candidates() -> None:
    assert len(list(AssignmentIterator().iterate(_children()))) == 24


def test_standalone_themed_assignment_iterator_generates_576_candidates() -> None:
    assert len(list(AssignmentIterator().iterate([*_children(), *_values()]))) == 576


def test_fixed_child_themed_assignment_iterator_generates_24_candidates() -> None:
    children = _children()
    values = _values()
    fixed = {child: Position(index + 1) for index, child in enumerate(children)}

    assignments = list(AssignmentIterator().iterate([*children, *values], fixed))

    assert len(assignments) == 24
    assert all(
        assignment.position_of(child) == fixed[child]
        for assignment in assignments
        for child in children
    )


def test_partially_fixed_category_uses_remaining_factorial_candidates() -> None:
    children = _children()
    fixed = {children[0]: Position(1), children[1]: Position(2)}

    assert len(list(AssignmentIterator().iterate(children, fixed))) == 2


def test_assignment_iterator_rejects_unknown_fixed_item() -> None:
    with pytest.raises(ValueError, match="not part of the assignment items"):
        list(AssignmentIterator().iterate(_children(), {Item("Z"): Position(1)}))


def test_assignment_iterator_rejects_duplicate_fixed_position() -> None:
    children = _children()
    with pytest.raises(ValueError, match="duplicate positions"):
        list(
            AssignmentIterator().iterate(
                children, {children[0]: Position(1), children[1]: Position(1)}
            )
        )

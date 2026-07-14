from __future__ import annotations

import pytest

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution


def test_puzzle_fixed_positions_are_read_only() -> None:
    child = Item("A")
    puzzle = Puzzle(items=[child], constraints=[], fixed_positions={child: Position(1)})

    with pytest.raises(TypeError):
        puzzle.fixed_positions[child] = Position(1)  # type: ignore[index]


def test_puzzle_rejects_fixed_non_child_item() -> None:
    value = Item("blue", category_id="colour")
    with pytest.raises(ValueError, match="only be supplied for child items"):
        Puzzle(items=[value], constraints=[], fixed_positions={value: Position(1)})


def test_puzzle_rejects_fixed_position_that_disagrees_with_solution() -> None:
    child = Item("A")
    solution = Solution(Assignment({child: Position(2)}))

    with pytest.raises(ValueError, match="agree with the puzzle solution"):
        Puzzle(
            items=[child], constraints=[], solution=solution, fixed_positions={child: Position(1)}
        )


def test_puzzle_fixed_positions_reject_common_mutation_methods() -> None:
    child = Item("A")
    puzzle = Puzzle(items=[child], constraints=[], fixed_positions={child: Position(1)})

    mutation_attempts = (
        lambda: puzzle.fixed_positions.clear(),  # type: ignore[attr-defined]
        lambda: puzzle.fixed_positions.pop(child),  # type: ignore[attr-defined]
        lambda: puzzle.fixed_positions.update({child: Position(1)}),  # type: ignore[attr-defined]
        lambda: puzzle.fixed_positions.setdefault(child, Position(1)),  # type: ignore[attr-defined]
        lambda: puzzle.fixed_positions.__ior__({child: Position(1)}),  # type: ignore[attr-defined]
    )
    for mutate in mutation_attempts:
        with pytest.raises((TypeError, AttributeError)):
            mutate()


def test_puzzle_fixed_positions_are_defensive_snapshot() -> None:
    child = Item("A")
    original = {child: Position(1)}
    puzzle = Puzzle(items=[child], constraints=[], fixed_positions=original)

    original.clear()

    assert dict(puzzle.fixed_positions) == {child: Position(1)}


def test_dict_copy_of_fixed_positions_is_independent() -> None:
    child = Item("A")
    puzzle = Puzzle(items=[child], constraints=[], fixed_positions={child: Position(1)})

    copied = dict(puzzle.fixed_positions)
    copied.clear()

    assert dict(puzzle.fixed_positions) == {child: Position(1)}


def test_two_puzzles_do_not_share_fixed_position_state() -> None:
    child = Item("A")
    source = {child: Position(1)}
    first = Puzzle(items=[child], constraints=[], fixed_positions=source)
    second = Puzzle(items=[child], constraints=[], fixed_positions=source)

    source.clear()

    assert dict(first.fixed_positions) == {child: Position(1)}
    assert dict(second.fixed_positions) == {child: Position(1)}
    assert first.fixed_positions is not second.fixed_positions


def test_clue_reducer_preserves_fixed_position_snapshot() -> None:
    from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
    from logical_puzzle_generator.generator.clue_reducer import ClueReducer
    from logical_puzzle_generator.model.clue import Clue
    from logical_puzzle_generator.model.clue_type import ClueType

    first, second = Item("A"), Item("B")
    constraint = LeftOfConstraint(first, second)
    clue = Clue(text="A is left of B", clue_type=ClueType.LEFT_OF, constraint=constraint)
    solution = Solution(Assignment({first: Position(1), second: Position(2)}))
    puzzle = Puzzle(
        items=[first, second],
        constraints=[constraint],
        clues=[clue],
        solution=solution,
        fixed_positions={first: Position(1), second: Position(2)},
    )

    reduced = ClueReducer().reduce(puzzle)

    assert dict(reduced.fixed_positions) == dict(puzzle.fixed_positions)
    assert reduced.fixed_positions is not puzzle.fixed_positions

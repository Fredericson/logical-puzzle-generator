from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator.solution_generator import SolutionGenerator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.tennis import create_template


def test_generate_returns_solution_with_complete_assignment() -> None:
    items = [Item("A"), Item("B"), Item("C"), Item("D")]

    solution = SolutionGenerator(random.Random(7)).generate(items)

    assert isinstance(solution, Solution)
    assert isinstance(solution.assignment, Assignment)
    assert set(solution.positions) == set(items)
    assert sorted(solution.positions.values()) == [
        Position(1),
        Position(2),
        Position(3),
        Position(4),
    ]
    assert solution.player_count == 4


def test_generate_uses_template_players_as_solution_items() -> None:
    template = create_template()

    solution = SolutionGenerator(random.Random(11)).generate(template)

    assert set(solution.positions) == set(template.players.items)
    assert sorted(solution.positions.values()) == [
        Position(1),
        Position(2),
        Position(3),
        Position(4),
    ]


def test_generate_accepts_puzzle_items() -> None:
    items = [Item("Lara"), Item("Mia"), Item("Tim"), Item("Noah")]
    puzzle = Puzzle(items=items, constraints=[])

    solution = SolutionGenerator(random.Random(13)).generate(puzzle)

    assert set(solution.positions) == set(items)
    assert sorted(solution.positions.values()) == [
        Position(1),
        Position(2),
        Position(3),
        Position(4),
    ]


def test_generate_is_deterministic_with_seeded_random_source() -> None:
    items = [Item("A"), Item("B"), Item("C"), Item("D")]

    first = SolutionGenerator(random.Random(23)).generate(items)
    second = SolutionGenerator(random.Random(23)).generate(items)

    assert first.positions == second.positions


def test_generate_rejects_empty_items() -> None:
    with pytest.raises(ValueError, match="at least one item"):
        SolutionGenerator(random.Random(1)).generate([])


def test_generate_rejects_duplicate_items() -> None:
    item = Item("A")

    with pytest.raises(ValueError, match="unique items"):
        SolutionGenerator(random.Random(1)).generate([item, item])


def test_generate_rejects_non_model_items() -> None:
    with pytest.raises(TypeError, match="model.Item"):
        SolutionGenerator(random.Random(1)).generate(["A", "B"])

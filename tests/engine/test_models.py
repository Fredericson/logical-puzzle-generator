from logical_puzzle_generator.model.category import Category, CategoryType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle


def test_canonical_puzzle_model_uses_items_and_constraints():
    players = Category(
        name="Children",
        type=CategoryType.PERSON,
        items=[Item("Lara"), Item("Tim")],
    )

    puzzle = Puzzle(items=players.items, constraints=[])

    assert puzzle.items == players.items
    assert puzzle.constraints == []
    assert puzzle.items[0].name == "Lara"

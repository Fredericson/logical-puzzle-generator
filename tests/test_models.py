from logical_puzzle_generator.models import (
    Category, CategoryType, Item, Puzzle, PuzzleConfig
)

def test_models():
    persons = Category(
        name="Children",
        type=CategoryType.PERSON,
        items=[Item("Lara"), Item("Tim")]
    )
    puzzle = Puzzle(
        categories=[persons],
        config=PuzzleConfig()
    )
    assert puzzle.config.players == 4
    assert puzzle.categories[0].items[0].name == "Lara"

from __future__ import annotations

from logical_puzzle_generator.generator.puzzle_template import PuzzleTemplate
from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.item import Item


def create_template() -> PuzzleTemplate:

    return PuzzleTemplate(

        title="Tennis Training",

        theme="Tennis",

        categories=[

            Category(
                "Players",
                [
                    Item("Aurelia"),
                    Item("Emma"),
                    Item("Lara"),
                    Item("Mia"),
                ],
            ),

            Category(
                "Shirt Colour",
                [
                    Item("Red"),
                    Item("Blue"),
                    Item("Yellow"),
                    Item("Green"),
                ],
            ),

            Category(
                "Racket Colour",
                [
                    Item("White"),
                    Item("Black"),
                    Item("Pink"),
                    Item("Orange"),
                ],
            ),

            Category(
                "Position",
                [
                    Item("1"),
                    Item("2"),
                    Item("3"),
                    Item("4"),
                ],
            ),
        ],
    )

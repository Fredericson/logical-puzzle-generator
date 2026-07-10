from __future__ import annotations

from collections.abc import Iterable

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle


class TextRenderer:
    """
    Renders domain objects into presentation text for printable output.

    The renderer intentionally uses public, human-readable model data and clue
    constraints. It does not expose constraint classes or perform generation,
    solving, or validation logic.
    """

    def __init__(self, language: Language | str = Language.ENGLISH) -> None:
        self.language = parse_language(language)

    def render(self, clues: Iterable[Clue]) -> list[str]:
        return self.render_clues(clues)

    def render_clues(self, clues: Iterable[Clue], item_count: int | None = None) -> list[str]:
        clue_renderer = ClueTextRenderer(self.language, item_count=item_count)
        lines: list[str] = []
        for index, clue in enumerate(clues, 1):
            lines.append(f"{index}. {clue_renderer.render_clue(clue)}")
        return lines

    def render_solution_rows(self, puzzle: Puzzle) -> list[tuple[str, str]]:
        if puzzle.solution is None:
            raise ValueError("Cannot render a solution PDF because the puzzle has no Solution.")

        assignment = puzzle.solution.assignment
        ordered_items = sorted(
            assignment.positions,
            key=lambda item: assignment.position_of(item).index,
        )
        return [
            (str(assignment.position_of(item).index), self.render_item_name(item))
            for item in ordered_items
        ]

    def render_item_name(self, item: Item) -> str:
        if not item.name:
            raise ValueError("Puzzle items must contain readable names.")
        return item.name

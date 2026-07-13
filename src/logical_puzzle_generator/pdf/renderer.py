from __future__ import annotations

import random

from collections.abc import Iterable

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


class TextRenderer:
    """
    Renders domain objects into presentation text for printable output.

    The renderer intentionally uses public, human-readable model data and clue
    constraints. It does not expose constraint classes or perform generation,
    solving, or validation logic.
    """

    def __init__(
        self,
        language: Language | str = Language.ENGLISH,
        random_source: random.Random | None = None,
    ) -> None:
        self.language = parse_language(language)
        self._random = random_source if random_source is not None else random.Random()

    def render(self, clues: Iterable[Clue]) -> list[str]:
        return self.render_clues(clues)

    def render_clues(self, clues: Iterable[Clue], item_count: int | None = None) -> list[str]:
        clue_renderer = ClueTextRenderer(
            self.language, item_count=item_count, random_source=self._random
        )
        lines: list[str] = []
        for index, clue in enumerate(clues, 1):
            lines.append(f"{index}. {clue_renderer.render_clue(clue)}")
        return lines

    def render_solution_rows(self, puzzle: Puzzle) -> list[tuple[str, str]]:
        if puzzle.solution is None:
            raise ValueError("Cannot render a solution PDF because the puzzle has no Solution.")

        assignment = puzzle.solution.assignment
        children = [item for item in puzzle.items if item.category_id == "children"]
        theme_items = [item for item in puzzle.items if item.category_id != "children"]
        rows: list[tuple[str, str]] = []
        for position in range(1, len(children) + 1):
            child = next(item for item in children if assignment.position_of(item).index == position)
            theme = next((item for item in theme_items if assignment.position_of(item).index == position), None)
            label = self.render_item_name(child)
            if theme is not None:
                label = f"{label} / {self.render_item_name(theme, puzzle=puzzle, short=True)}"
            rows.append((str(position), label))
        return rows

    def render_item_name(self, item: Item, puzzle: Puzzle | None = None, *, short: bool = False) -> str:
        if not item.name:
            raise ValueError("Puzzle items must contain readable names.")
        if item.category_id != "children" and puzzle is not None and puzzle.metadata is not None:
            theme = DEFAULT_THEME_REGISTRY.resolve(puzzle.metadata.theme_id)
            for value in theme.values:
                if value.id == item.name:
                    return value.display(self.language, short=short)
        return item.name

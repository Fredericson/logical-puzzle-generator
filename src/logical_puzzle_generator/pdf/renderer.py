from __future__ import annotations

import random

from collections.abc import Iterable

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver

SolutionRow = tuple[str, str] | tuple[str, str, str]


class TextRenderer:
    """
    Renders domain objects into presentation text for printable output.
    """

    def __init__(
        self,
        language: Language | str = Language.ENGLISH,
        random_source: random.Random | None = None,
        presentation_resolver: ItemPresentationResolver | None = None,
    ) -> None:
        self.language = parse_language(language)
        self._random = random_source if random_source is not None else random.Random()
        self._resolver = presentation_resolver

    def render(self, clues: Iterable[Clue]) -> list[str]:
        return self.render_clues(clues)

    def render_clues(
        self,
        clues: Iterable[Clue],
        item_count: int | None = None,
        presentation_resolver: ItemPresentationResolver | None = None,
    ) -> list[str]:
        clue_renderer = ClueTextRenderer(
            self.language,
            item_count=item_count,
            random_source=self._random,
            presentation_resolver=presentation_resolver or self._resolver,
        )
        return [
            f"{index}. {clue_renderer.render_clue(clue)}" for index, clue in enumerate(clues, 1)
        ]

    def render_solution_rows(
        self,
        puzzle: Puzzle,
        presentation_resolver: ItemPresentationResolver | None = None,
    ) -> list[SolutionRow]:
        if puzzle.solution is None:
            raise ValueError("Cannot render a solution PDF because the puzzle has no Solution.")

        assignment = puzzle.solution.assignment
        children = [item for item in puzzle.items if item.category_id == CHILDREN_CATEGORY_ID]
        theme_items = [
            item
            for category in puzzle.categories
            for item in category.items
            if item.category_id != CHILDREN_CATEGORY_ID
        ]
        rows: list[SolutionRow] = []
        for position in range(1, len(children) + 1):
            child = next(
                item for item in children if assignment.position_of(item).index == position
            )
            theme = next(
                (item for item in theme_items if assignment.position_of(item).index == position),
                None,
            )
            theme_label = (
                ""
                if theme is None
                else self._resolver_required(presentation_resolver).short_theme_label(theme)
            )
            if theme is None:
                rows.append((str(position), self.render_item_name(child, presentation_resolver)))
            else:
                rows.append(
                    (
                        str(position),
                        self.render_item_name(child, presentation_resolver),
                        theme_label,
                    )
                )
        return rows

    def _resolver_required(
        self, resolver: ItemPresentationResolver | None
    ) -> ItemPresentationResolver:
        if resolver is None:
            raise ValueError("A presentation resolver is required for thematic item names.")
        return resolver

    def render_item_name(
        self,
        item: Item,
        presentation_resolver: ItemPresentationResolver | None = None,
        *,
        short: bool = False,
    ) -> str:
        resolver = presentation_resolver or self._resolver
        if resolver is not None:
            return resolver.item_label(item, short=short)
        if item.category_id != CHILDREN_CATEGORY_ID:
            raise ValueError("A presentation resolver is required for thematic item names.")
        if not item.name:
            raise ValueError("Puzzle items must contain readable names.")
        return item.name

from __future__ import annotations

from dataclasses import dataclass, field

from logical_puzzle_generator.themes.registry import DEFAULT_THEME_ID


@dataclass(slots=True)
class Metadata:
    """Metadata describing one generated puzzle."""

    title: str
    theme: str
    difficulty: int
    theme_id: str = DEFAULT_THEME_ID
    theme_category_id: str = "training"
    theme_category_instance_id: str = "training_1"
    selected_theme_value_ids: tuple[str, ...] = field(default_factory=tuple)
    author: str = "Logical Puzzle Generator"
    version: str = "1.0.0"

    @property
    def thematic_category_id(self) -> str:
        return self.theme_category_id

    @thematic_category_id.setter
    def thematic_category_id(self, value: str) -> None:
        self.theme_category_id = value

    @property
    def thematic_category_label(self) -> str:
        return self.theme_category_id

    @thematic_category_label.setter
    def thematic_category_label(self, value: str) -> None:
        self.theme_category_id = value

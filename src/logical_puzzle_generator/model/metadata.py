from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Metadata:
    """Metadata describing one generated puzzle."""

    title: str
    theme: str
    difficulty: int
    theme_id: str | None = None
    theme_category_id: str | None = None
    theme_category_instance_id: str | None = None
    selected_theme_value_ids: tuple[str, ...] = field(default_factory=tuple)
    author: str = "Logical Puzzle Generator"
    version: str = "1.0.0"

    @property
    def thematic_category_id(self) -> str | None:
        """Deprecated alias for the canonical theme_category_id field."""
        return self.theme_category_id

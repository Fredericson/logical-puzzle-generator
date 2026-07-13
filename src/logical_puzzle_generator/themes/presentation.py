from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.themes.registry import ThemeCategoryInstance, ThemeDefinition


@dataclass(frozen=True, slots=True)
class ItemPresentationResolver:
    theme: ThemeDefinition
    category_instance: ThemeCategoryInstance
    language: Language | str = Language.ENGLISH

    def __post_init__(self) -> None:
        object.__setattr__(self, "language", parse_language(self.language))

    @property
    def category(self):
        return self.category_instance.definition

    def is_child(self, item: Item) -> bool:
        return item.category_id == CHILDREN_CATEGORY_ID

    def child_label(self, item: Item) -> str:
        if not self.is_child(item):
            raise ValueError(f"Expected child item, got category '{item.category_id}'.")
        return item.name

    def theme_value(self, item: Item):
        if self.is_child(item):
            raise ValueError("Expected thematic item, got child item.")
        if item.category_id != self.category.id:
            raise ValueError(f"Expected thematic item from category '{self.category.id}', got '{item.category_id}'.")
        return self.category.value_by_id(item.name)

    def item_label(self, item: Item, *, short: bool = False) -> str:
        if self.is_child(item):
            return item.name
        return self.theme_value(item).display(self.language, short=short)

    def short_theme_label(self, item: Item) -> str:
        return self.item_label(item, short=True)

    def long_theme_label(self, item: Item) -> str:
        return self.item_label(item, short=False)

    def theme_subject_phrase(self, item: Item) -> str:
        value = self.theme_value(item)
        return value.subject(self.language)

    def child_with_theme_phrase(self, item: Item, *, dative: bool = False) -> str:
        value = self.theme_value(item)
        wording = self.category.wording
        template = (
            wording.child_with_theme_dative if dative else wording.child_with_theme_nominative
        ).for_language(self.language)
        return template.format(theme=value.display(self.language), theme_subject=value.subject(self.language))

    def direct_assignment_sentence(self, child: Item, theme_item: Item) -> str:
        template = self.category.wording.direct_assignment.for_language(self.language)
        value = self.theme_value(theme_item)
        return template.format(
            child=self.child_label(child),
            theme=value.display(self.language),
            theme_subject=value.subject(self.language),
        )

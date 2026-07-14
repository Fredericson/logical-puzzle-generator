from __future__ import annotations

import random

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.constraints.numeric import (
    ExactNumericValueConstraint,
    NumericDifferenceConstraint,
    NumericMultipleConstraint,
)
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.template_catalog import TemplateCatalog
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver


class ClueTextRenderer:
    """Render clue text in a selected presentation language."""

    def __init__(
        self,
        language: Language | str = Language.ENGLISH,
        item_count: int | None = None,
        random_source: random.Random | None = None,
        presentation_resolver: ItemPresentationResolver | None = None,
    ) -> None:
        self.language = parse_language(language)
        self.item_count = item_count
        self._random = random_source if random_source is not None else random.Random()
        self._templates = TemplateCatalog(self.language)
        self._resolver = presentation_resolver

    def render_clue(self, clue: Clue) -> str:
        constraint = clue.constraint
        if isinstance(constraint, FixedPositionConstraint):
            return self._render_fixed_position(constraint)
        if isinstance(constraint, DirectLeftOfConstraint):
            return self._render_relation("direct_left", constraint.left, constraint.right)
        if isinstance(constraint, LeftOfConstraint):
            return self._render_relation("left", constraint.left, constraint.right)
        if isinstance(constraint, DirectRightOfConstraint):
            return self._render_relation("direct_right", constraint.right, constraint.left)
        if isinstance(constraint, RightOfConstraint):
            return self._render_relation("right", constraint.right, constraint.left)
        if isinstance(constraint, AdjacentConstraint):
            return self._render_relation("adjacent", constraint.first, constraint.second)
        if isinstance(constraint, SamePositionConstraint):
            child, value = self._child_theme_pair(constraint.first, constraint.second)
            return self._resolver_required().direct_assignment_sentence(child, value)
        if isinstance(constraint, ExactNumericValueConstraint):
            return self._render_numeric_exact(constraint)
        if isinstance(constraint, NumericDifferenceConstraint):
            return self._render_numeric_difference(constraint)
        if isinstance(constraint, NumericMultipleConstraint):
            return self._render_numeric_multiple(constraint)
        raise TypeError(f"Unsupported constraint type: {constraint.__class__.__name__}.")

    def _numeric_unit(self, value: int) -> str:
        wording = self._resolver_required().category.wording
        text = wording.unit_singular if value == 1 else wording.unit_plural
        if text is None:
            raise ValueError("Numeric category wording requires units.")
        return text.for_language(self.language)

    def _numeric_text(self, text) -> str:
        if text is None:
            raise ValueError("Numeric category wording is incomplete.")
        return text.for_language(self.language)

    def _render_numeric_exact(self, constraint: ExactNumericValueConstraint) -> str:
        wording = self._resolver_required().category.wording
        return self._numeric_text(wording.numeric_exact).format(
            child=self._label(constraint.child),
            value=constraint.value,
            unit=self._numeric_unit(constraint.value),
        )

    def _render_numeric_difference(self, constraint: NumericDifferenceConstraint) -> str:
        use_more = self._random.choice([True, False])
        wording = self._resolver_required().category.wording
        template = wording.numeric_more if use_more else wording.numeric_fewer
        return self._numeric_text(template).format(
            greater=self._label(constraint.greater_child),
            lesser=self._label(constraint.lesser_child),
            difference=constraint.difference,
            unit=self._numeric_unit(constraint.difference),
        )

    def _render_numeric_multiple(self, constraint: NumericMultipleConstraint) -> str:
        wording = self._resolver_required().category.wording
        return self._numeric_text(wording.numeric_twice).format(
            multiple=self._label(constraint.multiple_child),
            base=self._label(constraint.base_child),
        )

    def _render_fixed_position(self, constraint: FixedPositionConstraint) -> str:
        item = constraint.item
        position = str(constraint.position.index)
        if self._is_child(item):
            return self._render_template(
                FixedPositionConstraint, {"A": self._label(item), "position": position}
            )
        value = self._resolver_required().theme_value(item)
        if value.numeric_value is not None:
            wording = self._resolver_required().category.wording
            return self._numeric_text(wording.numeric_position_exact).format(
                position=position,
                value=value.numeric_value,
                unit=self._numeric_unit(value.numeric_value),
            )
        subject = (
            self._resolver_required().theme_position_subject_phrase(item)
            if value.position_subject_phrase is not None
            else self._resolver_required().child_with_theme_phrase(item)
        )
        if self.language is Language.GERMAN:
            return "{subject} befindet sich auf Position {position}.".format(
                subject=subject,
                position=position,
            )
        return "{subject} is in Position {position}.".format(
            subject=subject,
            position=position,
        )

    def _render_relation(self, relation: str, first: Item, second: Item) -> str:
        if self._is_child(first) and self._is_child(second):
            mapping = {
                "direct_left": DirectLeftOfConstraint,
                "left": LeftOfConstraint,
                "direct_right": DirectRightOfConstraint,
                "right": RightOfConstraint,
                "adjacent": AdjacentConstraint,
            }
            key = mapping[relation]
            values = {"A": self._label(first), "B": self._label(second)}
            return self._render_template(key, values)

        subject = self._standing_phrase(first, dative=False)
        target = self._standing_phrase(second, dative=self.language is Language.GERMAN)
        templates = self._relation_templates()[relation]
        return templates.format(subject=subject, target=target)

    def _relation_templates(self) -> dict[str, str]:
        if self.language is Language.GERMAN:
            return {
                "direct_left": "{subject} steht direkt links von {target}.",
                "left": "{subject} steht links von {target}.",
                "direct_right": "{subject} steht direkt rechts von {target}.",
                "right": "{subject} steht rechts von {target}.",
                "adjacent": "{subject} steht neben {target}.",
            }
        return {
            "direct_left": "{subject} stands directly left of {target}.",
            "left": "{subject} stands left of {target}.",
            "direct_right": "{subject} stands directly right of {target}.",
            "right": "{subject} stands right of {target}.",
            "adjacent": "{subject} stands next to {target}.",
        }

    def _standing_phrase(self, item: Item, *, dative: bool) -> str:
        if self._is_child(item):
            return self._label(item)
        return self._resolver_required().child_with_theme_phrase(item, dative=dative)

    def _child_theme_pair(self, first: Item, second: Item) -> tuple[Item, Item]:
        if self._is_child(first) and not self._is_child(second):
            return first, second
        if self._is_child(second) and not self._is_child(first):
            return second, first
        raise ValueError("SamePositionConstraint clue requires one child and one thematic item.")

    def _label(self, item: Item) -> str:
        if self._resolver is not None:
            return self._resolver.item_label(item)
        if not self._is_child(item):
            raise ValueError("A presentation resolver is required for thematic clue text.")
        return item.name

    def _is_child(self, item: Item) -> bool:
        return item.category_id == CHILDREN_CATEGORY_ID

    def _resolver_required(self) -> ItemPresentationResolver:
        if self._resolver is None:
            raise ValueError("A presentation resolver is required for thematic clue text.")
        return self._resolver

    def _render_template(self, constraint_type, values: dict[str, str]) -> str:
        template = self._random.choice(self._templates.templates_for(constraint_type))
        missing = template.placeholders - values.keys()
        if missing:
            missing_names = ", ".join(sorted(missing))
            raise ValueError(f"Missing template placeholder values: {missing_names}.")
        return template.text.format(**values)

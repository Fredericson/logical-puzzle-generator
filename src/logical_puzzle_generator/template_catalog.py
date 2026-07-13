from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from string import Formatter
from typing import Final

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.localization import Language, parse_language

ConstraintType = type[Constraint]


@dataclass(frozen=True, slots=True)
class ClueTemplate:
    """A localized sentence template plus the placeholders it requires."""

    text: str
    placeholders: frozenset[str]


class TemplateCatalog:
    """Central catalog for localized clue wording templates."""

    _TEMPLATES: Final[Mapping[Language, Mapping[ConstraintType, tuple[str, ...]]]] = {
        Language.ENGLISH: {
            FixedPositionConstraint: (
                "{A} stands at position {position}.",
                "Position {position} belongs to {A}.",
                "In position {position} stands {A}.",
            ),
            DirectLeftOfConstraint: (
                "{A} stands directly left of {B}.",
                "{B} stands directly right of {A}.",
                "Immediately to the left of {B} stands {A}.",
            ),
            LeftOfConstraint: (
                "{A} stands left of {B}.",
                "{B} stands right of {A}.",
                "To the left of {B} stands {A}.",
            ),
            DirectRightOfConstraint: (
                "{A} stands directly right of {B}.",
                "{B} stands directly left of {A}.",
                "Immediately to the right of {B} stands {A}.",
            ),
            RightOfConstraint: (
                "{A} stands right of {B}.",
                "{B} stands left of {A}.",
                "To the right of {B} stands {A}.",
            ),
            AdjacentConstraint: (
                "{A} stands next to {B}.",
                "{A} and {B} stand beside each other.",
                "{B} stands next to {A}.",
            ),
            SamePositionConstraint: (
                "{A} has {B}.",
                "{B} belongs to {A}.",
            ),
        },
        Language.GERMAN: {
            FixedPositionConstraint: (
                "{A} steht auf Position {position}.",
                "Position {position} gehört zu {A}.",
                "Auf Position {position} steht {A}.",
            ),
            DirectLeftOfConstraint: (
                "{A} steht direkt links von {B}.",
                "{B} steht direkt rechts von {A}.",
                "Direkt links von {B} steht {A}.",
            ),
            LeftOfConstraint: (
                "{A} steht links von {B}.",
                "Rechts von {A} steht {B}.",
                "Links von {B} steht {A}.",
            ),
            DirectRightOfConstraint: (
                "{A} steht direkt rechts von {B}.",
                "{B} steht direkt links von {A}.",
                "Direkt rechts von {B} steht {A}.",
            ),
            RightOfConstraint: (
                "{A} steht rechts von {B}.",
                "Links von {A} steht {B}.",
                "Rechts von {B} steht {A}.",
            ),
            AdjacentConstraint: (
                "{A} steht neben {B}.",
                "{A} und {B} stehen nebeneinander.",
                "{B} steht neben {A}.",
            ),
            SamePositionConstraint: (
                "{A} hat {B}.",
                "{B} gehört zu {A}.",
            ),
        },
    }

    def __init__(self, language: Language | str = Language.ENGLISH) -> None:
        self.language = parse_language(language)

    def templates_for(self, constraint_type: ConstraintType) -> tuple[ClueTemplate, ...]:
        try:
            templates = self._TEMPLATES[self.language][constraint_type]
        except KeyError as exc:
            raise TypeError(f"Unsupported constraint type: {constraint_type.__name__}.") from exc
        return tuple(ClueTemplate(text, _placeholders(text)) for text in templates)

    def template_texts_for(self, constraint_type: ConstraintType) -> tuple[str, ...]:
        return tuple(template.text for template in self.templates_for(constraint_type))

    @classmethod
    def visible_constraint_types(cls) -> tuple[ConstraintType, ...]:
        return (
            FixedPositionConstraint,
            DirectLeftOfConstraint,
            LeftOfConstraint,
            DirectRightOfConstraint,
            RightOfConstraint,
            AdjacentConstraint,
            SamePositionConstraint,
        )

    @classmethod
    def languages(cls) -> Sequence[Language]:
        return tuple(cls._TEMPLATES)


def _placeholders(template: str) -> frozenset[str]:
    return frozenset(
        field_name for _, field_name, _, _ in Formatter().parse(template) if field_name is not None
    )

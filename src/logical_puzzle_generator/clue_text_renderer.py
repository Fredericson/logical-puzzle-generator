from __future__ import annotations

import random

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.template_catalog import TemplateCatalog
from logical_puzzle_generator.model.clue import Clue


class ClueTextRenderer:
    """Render clue text in a selected presentation language."""

    def __init__(
        self,
        language: Language | str = Language.ENGLISH,
        item_count: int | None = None,
        random_source: random.Random | None = None,
    ) -> None:
        self.language = parse_language(language)
        self.item_count = item_count
        self._random = random_source if random_source is not None else random.Random()
        self._templates = TemplateCatalog(self.language)

    def render_clue(self, clue: Clue) -> str:
        constraint = clue.constraint
        if isinstance(constraint, FixedPositionConstraint):
            return self._render_template(
                FixedPositionConstraint,
                {"A": constraint.item.name, "position": str(constraint.position.index)},
            )
        if isinstance(constraint, DirectLeftOfConstraint):
            return self._render_template(
                DirectLeftOfConstraint,
                {"A": constraint.left.name, "B": constraint.right.name},
            )
        if isinstance(constraint, LeftOfConstraint):
            return self._render_template(
                LeftOfConstraint,
                {"A": constraint.left.name, "B": constraint.right.name},
            )
        if isinstance(constraint, DirectRightOfConstraint):
            return self._render_template(
                DirectRightOfConstraint,
                {"A": constraint.right.name, "B": constraint.left.name},
            )
        if isinstance(constraint, RightOfConstraint):
            return self._render_template(
                RightOfConstraint,
                {"A": constraint.right.name, "B": constraint.left.name},
            )
        if isinstance(constraint, AdjacentConstraint):
            return self._render_template(
                AdjacentConstraint,
                {"A": constraint.first.name, "B": constraint.second.name},
            )
        raise TypeError(f"Unsupported constraint type: {constraint.__class__.__name__}.")

    def _render_template(self, constraint_type, values: dict[str, str]) -> str:
        template = self._random.choice(self._templates.templates_for(constraint_type))
        missing = template.placeholders - values.keys()
        if missing:
            missing_names = ", ".join(sorted(missing))
            raise ValueError(f"Missing template placeholder values: {missing_names}.")
        return template.text.format(**values)

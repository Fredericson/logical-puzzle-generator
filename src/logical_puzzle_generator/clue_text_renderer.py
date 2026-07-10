from __future__ import annotations

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.clue import Clue


class ClueTextRenderer:
    """Render clue text in a selected presentation language."""

    def __init__(self, language: Language | str = Language.ENGLISH, item_count: int | None = None) -> None:
        self.language = parse_language(language)
        self.item_count = item_count

    def render_clue(self, clue: Clue) -> str:
        if self.language is Language.ENGLISH:
            if not clue.text:
                raise ValueError("Puzzle clues must contain human-readable text.")
            return clue.text
        return self._render_german(clue)

    def _render_german(self, clue: Clue) -> str:
        constraint = clue.constraint
        if isinstance(constraint, FixedPositionConstraint):
            if constraint.position.index == 1:
                return f"{constraint.item.name} steht ganz links."
            if self.item_count is not None and constraint.position.index == self.item_count:
                return f"{constraint.item.name} steht ganz rechts."
            return f"{constraint.item.name} steht auf Position {constraint.position.index}."
        if isinstance(constraint, DirectLeftOfConstraint):
            return f"{constraint.left.name} steht direkt links von {constraint.right.name}."
        if isinstance(constraint, LeftOfConstraint):
            return f"{constraint.left.name} steht links von {constraint.right.name}."
        if isinstance(constraint, DirectRightOfConstraint):
            return f"{constraint.right.name} steht direkt rechts von {constraint.left.name}."
        if isinstance(constraint, RightOfConstraint):
            return f"{constraint.right.name} steht rechts von {constraint.left.name}."
        if isinstance(constraint, AdjacentConstraint):
            return f"{constraint.first.name} steht neben {constraint.second.name}."
        raise TypeError(f"Unsupported constraint type: {constraint.__class__.__name__}.")

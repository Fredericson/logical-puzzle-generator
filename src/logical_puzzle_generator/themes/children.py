from __future__ import annotations

import random
from typing import Final

from logical_puzzle_generator.model.item import Item

DEFAULT_CHILD_NAME_POOL: Final[tuple[str, ...]] = ("Aurelia", "Emma", "Lara", "Mia")
DEFAULT_CHILD_COUNT: Final = 4


def select_child_items(
    random_source: random.Random,
    *,
    count: int = DEFAULT_CHILD_COUNT,
    name_pool: tuple[str, ...] = DEFAULT_CHILD_NAME_POOL,
) -> tuple[Item, ...]:
    if count < 1:
        raise ValueError("Child count must be positive.")
    if count > len(name_pool):
        raise ValueError("Child count cannot exceed the available child name pool.")
    return tuple(Item(name) for name in random_source.sample(name_pool, k=count))

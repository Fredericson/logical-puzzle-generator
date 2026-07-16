from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.random_streams import derive_seed, derived_random


def test_derive_seed_is_stable_by_seed_and_namespace() -> None:
    assert derive_seed(42, "puzzle_book.difficulty") == derive_seed(42, "puzzle_book.difficulty")


def test_derive_seed_separates_namespaces_and_base_seeds() -> None:
    assert derive_seed(42, "puzzle_book.difficulty") != derive_seed(42, "puzzle_book.categories")
    assert derive_seed(42, "puzzle_book.difficulty") != derive_seed(43, "puzzle_book.difficulty")


@pytest.mark.parametrize("invalid_seed", [True, False, 1.5, "42", None])
def test_derive_seed_rejects_invalid_base_seed(invalid_seed) -> None:
    with pytest.raises(TypeError, match="Base seed"):
        derive_seed(invalid_seed, "namespace")


@pytest.mark.parametrize("invalid_namespace", ["", 7, None])
def test_derive_seed_rejects_invalid_namespace(invalid_namespace) -> None:
    with pytest.raises(ValueError, match="namespace"):
        derive_seed(42, invalid_namespace)


def test_derived_random_uses_the_derived_seed() -> None:
    first = derived_random(42, "puzzle_book.difficulty")
    second = random.Random(derive_seed(42, "puzzle_book.difficulty"))

    assert [first.random() for _ in range(3)] == [second.random() for _ in range(3)]

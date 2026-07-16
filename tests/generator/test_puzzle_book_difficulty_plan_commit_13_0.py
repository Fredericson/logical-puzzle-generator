from __future__ import annotations

from collections import Counter
import random

import pytest

from logical_puzzle_generator.generator.difficulty import (
    CONCRETE_DIFFICULTIES,
    Difficulty,
    PuzzleBookDifficultyPlanner,
)


def _all_pages(plan):
    return (plan.position_difficulty, *plan.theme_page_difficulties)


def _max_run(values):
    longest = current = 0
    previous = None
    for value in values:
        current = current + 1 if value is previous else 1
        longest = max(longest, current)
        previous = value
    return longest


@pytest.mark.parametrize("difficulty", [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
@pytest.mark.parametrize("count", [0, 1, 5, 14])
def test_uniform_plans_are_concrete_and_do_not_consume_randomness(difficulty, count) -> None:
    rng = random.Random(123)
    before = rng.getstate()

    plan = PuzzleBookDifficultyPlanner(rng).uniform(difficulty, count)

    assert rng.getstate() == before
    assert plan.position_difficulty is difficulty
    assert plan.theme_page_difficulties == (difficulty,) * count


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 5, 6, 7, 8, 14, 100])
def test_mixed_plans_balance_all_puzzle_pages(count) -> None:
    plan = PuzzleBookDifficultyPlanner(random.Random(42)).mixed(theme_page_count=count)
    all_pages = _all_pages(plan)
    counts = Counter(all_pages)
    totals = [counts[difficulty] for difficulty in CONCRETE_DIFFICULTIES]

    assert len(all_pages) == count + 1
    assert len(plan.theme_page_difficulties) == count
    assert max(totals) - min(totals) <= 1
    if len(all_pages) >= 3:
        assert all(counts[difficulty] > 0 for difficulty in CONCRETE_DIFFICULTIES)
    if len(all_pages) == 3:
        assert totals == [1, 1, 1]


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 42, 99])
@pytest.mark.parametrize("count", [2, 3, 4, 5, 6, 8, 14, 100])
def test_mixed_plans_prevent_runs_longer_than_two_across_all_pages(seed, count) -> None:
    plan = PuzzleBookDifficultyPlanner(random.Random(seed)).mixed(theme_page_count=count)

    assert _max_run(_all_pages(plan)) <= 2


def test_mixed_plans_are_deterministic_and_seeded() -> None:
    first = PuzzleBookDifficultyPlanner(random.Random(42)).mixed(theme_page_count=8)
    second = PuzzleBookDifficultyPlanner(random.Random(42)).mixed(theme_page_count=8)
    different = PuzzleBookDifficultyPlanner(random.Random(43)).mixed(theme_page_count=8)

    assert first == second
    assert _all_pages(first) != _all_pages(different)


def test_position_page_participates_in_mixed_distribution() -> None:
    plans = [
        PuzzleBookDifficultyPlanner(random.Random(seed)).mixed(theme_page_count=2)
        for seed in (0, 3, 13)
    ]

    assert {plan.position_difficulty for plan in plans} == set(CONCRETE_DIFFICULTIES)
    for plan in plans:
        assert Counter(_all_pages(plan)) == Counter(CONCRETE_DIFFICULTIES)

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator import Difficulty, PuzzleGenerator
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.tennis import create_template

RELATION_TYPES = (
    DirectLeftOfConstraint,
    LeftOfConstraint,
    DirectRightOfConstraint,
    RightOfConstraint,
    AdjacentConstraint,
)
RELATION_TYPE_NAMES = tuple(relation_type.__name__ for relation_type in RELATION_TYPES)

# Commit 12.0 statistical gate: 200 explicit integer seeds per difficulty,
# using non-overlapping ranges so failures identify the difficulty quickly.
SAMPLE_SEED_RANGES = {
    Difficulty.EASY: range(10_000, 10_200),
    Difficulty.MEDIUM: range(20_000, 20_200),
    Difficulty.HARD: range(30_000, 30_200),
}
SMALL_REGRESSION_SEEDS = range(12_000, 12_012)

# These thresholds are deterministic quality gates, not mathematical correctness
# rules. They were chosen to catch starvation regressions where supported relation
# meanings disappear or become overwhelmingly dominant. If generation policy is
# intentionally improved, update these constants with a freshly measured,
# deterministic baseline and keep the documentation architecture-focused.
MIN_RELATION_SHARE = 0.05
MAX_RELATION_SHARE = 0.50
MIN_ORDINARY_RELATION_SHARE = 0.10


@dataclass(frozen=True)
class RelationDistribution:
    counts: Counter[str]
    difficulty_sample_sizes: dict[Difficulty, int]
    seed_ranges: dict[Difficulty, range]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


class GeneratedSample(Iterable[tuple[Difficulty, Puzzle]]):
    def __init__(self, seed_ranges: dict[Difficulty, range]) -> None:
        self.seed_ranges = seed_ranges

    def __iter__(self) -> Iterable[tuple[Difficulty, Puzzle]]:
        template = create_template()
        for difficulty, seeds in self.seed_ranges.items():
            for seed in seeds:
                generator = PuzzleGenerator(
                    random_source=random.Random(seed),
                    difficulty=difficulty,
                )
                yield difficulty, generator.generate(template)


def generate_sample(seed_ranges: dict[Difficulty, range]) -> GeneratedSample:
    return GeneratedSample(seed_ranges)


def count_relation_types(puzzles: Iterable[tuple[Difficulty, Puzzle]]) -> Counter[str]:
    counts: Counter[str] = Counter({relation_name: 0 for relation_name in RELATION_TYPE_NAMES})
    for _difficulty, puzzle in puzzles:
        for constraint in puzzle.constraints:
            for relation_type in RELATION_TYPES:
                if isinstance(constraint, relation_type):
                    counts[relation_type.__name__] += 1
                    break
    return counts


def assert_puzzle_invariants(difficulty: Difficulty, puzzle: Puzzle) -> None:
    fixed_count = sum(
        isinstance(constraint, FixedPositionConstraint) for constraint in puzzle.constraints
    )
    relation_count = sum(
        isinstance(constraint, relation_type)
        for constraint in puzzle.constraints
        for relation_type in RELATION_TYPES
    )
    expected_fixed_counts = {
        Difficulty.EASY: 2,
        Difficulty.MEDIUM: 1,
        Difficulty.HARD: 0,
    }

    assert len(puzzle.clues) == 3
    assert len(puzzle.constraints) == 3
    assert fixed_count == expected_fixed_counts[difficulty]
    assert relation_count == 3 - expected_fixed_counts[difficulty]
    assert puzzle.solution is not None

    result = Solver().solve(puzzle, stop_after=2)
    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment


def relation_share(distribution: RelationDistribution, relation_name: str) -> float:
    return distribution.counts[relation_name] / distribution.total


def distribution_diagnostics(distribution: RelationDistribution) -> str:
    lines = [
        "Relation distribution regression:",
        f"total={distribution.total}",
        "difficulty sample sizes="
        + ", ".join(
            f"{difficulty.cli_value}:{sample_size}"
            for difficulty, sample_size in distribution.difficulty_sample_sizes.items()
        ),
        "seed ranges="
        + ", ".join(
            f"{difficulty.cli_value}:{seeds.start}-{seeds.stop - 1}"
            for difficulty, seeds in distribution.seed_ranges.items()
        ),
    ]
    for relation_name in RELATION_TYPE_NAMES:
        count = distribution.counts[relation_name]
        lines.append(f"{relation_name}={count} ({count / distribution.total:.2%})")
    return "\n".join(lines)


def build_distribution(seed_ranges: dict[Difficulty, range]) -> RelationDistribution:
    sample = list(generate_sample(seed_ranges))
    for difficulty, puzzle in sample:
        assert_puzzle_invariants(difficulty, puzzle)
    return RelationDistribution(
        counts=count_relation_types(sample),
        difficulty_sample_sizes={difficulty: len(seeds) for difficulty, seeds in seed_ranges.items()},
        seed_ranges=seed_ranges,
    )


def test_original_symptom_regression_sample_includes_ordinary_relation() -> None:
    seed_ranges = {Difficulty.HARD: SMALL_REGRESSION_SEEDS}
    distribution = build_distribution(seed_ranges)

    ordinary_count = (
        distribution.counts[LeftOfConstraint.__name__]
        + distribution.counts[RightOfConstraint.__name__]
    )
    assert ordinary_count > 0, distribution_diagnostics(distribution)


def test_relation_distribution_statistical_regression_gate() -> None:
    distribution = build_distribution(SAMPLE_SEED_RANGES)
    diagnostics = distribution_diagnostics(distribution)

    assert distribution.total == 1_200, diagnostics
    assert all(distribution.counts[relation_name] > 0 for relation_name in RELATION_TYPE_NAMES), (
        diagnostics
    )

    for relation_name in RELATION_TYPE_NAMES:
        share = relation_share(distribution, relation_name)
        assert share >= MIN_RELATION_SHARE, diagnostics
        assert share <= MAX_RELATION_SHARE, diagnostics

    ordinary_share = relation_share(
        distribution, LeftOfConstraint.__name__
    ) + relation_share(distribution, RightOfConstraint.__name__)
    assert ordinary_share >= MIN_ORDINARY_RELATION_SHARE, diagnostics


def test_relation_distribution_counts_are_deterministic() -> None:
    first = build_distribution(SAMPLE_SEED_RANGES)
    second = build_distribution(SAMPLE_SEED_RANGES)

    assert first.counts == second.counts, (
        distribution_diagnostics(first) + "\n\n" + distribution_diagnostics(second)
    )

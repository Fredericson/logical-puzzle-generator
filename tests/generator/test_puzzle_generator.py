from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    DirectLeftOfConstraint,
    DirectRightOfConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator import ClueGenerator
from logical_puzzle_generator.generator import puzzle_generator as puzzle_generator_module
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.generator.puzzle_template import PuzzleTemplate
from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.tennis import create_template


class RejectThenAcceptValidator:
    def __init__(self) -> None:
        self.calls = 0

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.calls += 1
        return self.calls > 1


class IdentityClueReducer:
    def reduce(self, puzzle: Puzzle) -> Puzzle:
        return puzzle


class RecordingValidator:
    def __init__(self) -> None:
        self.puzzles: list[Puzzle] = []

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.puzzles.append(puzzle)
        return True


def test_generate_returns_complete_unique_puzzle() -> None:
    template = create_template()

    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(template)

    assert puzzle.items == template.players.items
    assert puzzle.solution is not None
    assert puzzle.metadata is not None
    assert puzzle.metadata.title == template.title
    assert puzzle.metadata.theme == template.theme
    assert len(puzzle.clues) <= len(puzzle.constraints)
    assert len(puzzle.clues) == len({(clue.clue_type, clue.text) for clue in puzzle.clues})
    assert all(constraint.matches(puzzle.solution.assignment) for constraint in puzzle.constraints)
    assert len({clue.clue_type for clue in puzzle.clues}) >= 2


def test_generate_validates_uniqueness() -> None:
    validator = RecordingValidator()

    puzzle = PuzzleGenerator(
        random_source=random.Random(11),
        validator=validator,
        clue_reducer=IdentityClueReducer(),
        difficulty="easy",
    ).generate(create_template())

    assert len(validator.puzzles) >= 2
    assert validator.puzzles[-1].items == puzzle.items
    assert any(recorded.constraints == puzzle.constraints for recorded in validator.puzzles)
    assert any(recorded.clues == puzzle.clues for recorded in validator.puzzles)
    assert any(recorded.solution == puzzle.solution for recorded in validator.puzzles)
    assert all(
        validator.puzzles[index] == validator.puzzles[index + 1]
        for index in range(0, len(validator.puzzles), 2)
    )


def test_generate_retries_when_puzzle_is_not_unique() -> None:
    validator = RejectThenAcceptValidator()

    puzzle = PuzzleGenerator(
        random_source=random.Random(13),
        validator=validator,
        clue_reducer=IdentityClueReducer(),
        difficulty="easy",
        max_attempts=3,
    ).generate(create_template())

    assert validator.calls == 5
    assert puzzle.solution is not None


def test_generate_is_deterministic_with_seeded_random_source() -> None:
    template = create_template()

    first = PuzzleGenerator(random_source=random.Random(23)).generate(template)
    second = PuzzleGenerator(random_source=random.Random(23)).generate(template)

    assert first.solution is not None
    assert second.solution is not None
    assert first.solution.positions == second.solution.positions
    assert [constraint.description for constraint in first.constraints] == [
        constraint.description for constraint in second.constraints
    ]
    assert [clue.text for clue in first.clues] == [clue.text for clue in second.clues]


def test_generate_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="model.Item"):
        PuzzleGenerator(random_source=random.Random(1)).generate(["A", "B"])


def test_generate_rejects_empty_template() -> None:
    template = PuzzleTemplate(
        title="Empty",
        theme="Test",
        categories=[Category("Players", [])],
    )

    with pytest.raises(ValueError, match="at least one item"):
        PuzzleGenerator(random_source=random.Random(1)).generate(template)


def test_generate_fails_after_max_attempts() -> None:
    class RejectingValidator:
        def __init__(self) -> None:
            self.calls = 0

        def has_unique_solution(self, puzzle: Puzzle) -> bool:
            self.calls += 1
            return False

    validator = RejectingValidator()

    with pytest.raises(RuntimeError, match="Unable to generate"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=validator,
            max_attempts=2,
        ).generate(create_template())

    assert validator.calls == 2


def test_generate_supports_single_item_with_fixed_position_constraint() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(1), difficulty="medium").generate([Item("Solo")])

    assert len(puzzle.constraints) == 1
    assert isinstance(puzzle.constraints[0], FixedPositionConstraint)
    assert puzzle.solution is not None


def test_generate_rejects_duplicate_items() -> None:
    item = Item("A")

    with pytest.raises(ValueError, match="unique items"):
        PuzzleGenerator(random_source=random.Random(1)).generate([item, item])


class AlwaysUniqueValidator:
    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        return True


class EmptyClueGenerator:
    def generate(self, constraints: object) -> list[Clue]:
        return []


class InvalidSolutionGenerator:
    def generate(self, source: object) -> object:
        return "not a solution"


class EmptyClueReducer:
    def reduce(self, puzzle: Puzzle) -> Puzzle:
        return Puzzle(
            items=puzzle.items,
            constraints=puzzle.constraints,
            clues=[],
            metadata=puzzle.metadata,
            solution=puzzle.solution,
        )


class NonUniqueAfterReductionValidator:
    def __init__(self) -> None:
        self.calls = 0

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.calls += 1
        return self.calls % 2 == 1


class RecordingSolutionGenerator:
    def __init__(self) -> None:
        self.generated_positions: list[tuple[int, ...]] = []

    def generate(self, source: object) -> Solution:
        items = list(source)  # type: ignore[arg-type]
        positions = [Position(index) for index in range(1, len(items) + 1)]
        solution = Solution(Assignment(dict(zip(items, positions, strict=True))))
        self.generated_positions.append(
            tuple(solution.assignment.position_of(item).index for item in items)
        )
        return solution


def test_generate_rejects_invalid_generated_solution_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="solution generator did not return a Solution"):
        PuzzleGenerator(
            solution_generator=InvalidSolutionGenerator(),
            difficulty="hard",
            max_attempts=2,
        ).generate(create_template())


def test_generate_rejects_missing_clues_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="clue generation produced no clues"):
        PuzzleGenerator(
            random_source=random.Random(1),
            clue_generator=EmptyClueGenerator(),
            validator=AlwaysUniqueValidator(),
            max_attempts=1,
        ).generate(create_template())


def test_generate_rejects_invalid_clue_reduction_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="clue reduction returned invalid clues"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=AlwaysUniqueValidator(),
            clue_reducer=EmptyClueReducer(),
            max_attempts=1,
        ).generate(create_template())


def test_generate_retries_when_reduced_puzzle_is_not_unique() -> None:
    validator = NonUniqueAfterReductionValidator()

    with pytest.raises(RuntimeError, match="reduced clue set is not uniquely solvable"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=validator,
            clue_reducer=IdentityClueReducer(),
            max_attempts=2,
        ).generate(create_template())

    assert validator.calls == 4


def test_generate_retry_sequence_is_deterministic() -> None:
    class RejectingValidator:
        def has_unique_solution(self, puzzle: Puzzle) -> bool:
            return False

    items = [Item("A"), Item("B")]
    first_generator = RecordingSolutionGenerator()
    second_generator = RecordingSolutionGenerator()

    with pytest.raises(RuntimeError, match="not uniquely solvable before clue reduction"):
        PuzzleGenerator(
            solution_generator=first_generator,
            difficulty="hard",
            validator=RejectingValidator(),
            max_attempts=3,
        ).generate(items)

    with pytest.raises(RuntimeError, match="not uniquely solvable before clue reduction"):
        PuzzleGenerator(
            solution_generator=second_generator,
            difficulty="hard",
            validator=RejectingValidator(),
            max_attempts=3,
        ).generate(items)

    assert first_generator.generated_positions == second_generator.generated_positions
    assert first_generator.generated_positions == [(1, 2), (1, 2), (1, 2)]


def test_generate_includes_attempt_count_in_exhaustion_message() -> None:
    with pytest.raises(RuntimeError, match="within 2 attempts.*Last failure: attempt 2"):
        PuzzleGenerator(
            random_source=random.Random(1),
            clue_generator=EmptyClueGenerator(),
            max_attempts=2,
        ).generate(create_template())


def test_four_item_left_of_single_visible_clue_is_not_unique() -> None:
    items = [Item("Emma"), Item("Aurelia"), Item("Mia"), Item("Lara")]
    constraint = LeftOfConstraint(items[0], items[1])
    puzzle = Puzzle(
        items=items,
        constraints=[constraint],
        clues=ClueGenerator().generate([constraint]),
    )

    result = Solver().solve(puzzle, stop_after=2)

    assert not result.has_unique_solution
    assert result.solution_count == 2


def test_generated_reduced_puzzle_solves_to_target_solution_from_visible_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())

    assert puzzle.solution is not None
    assert len(puzzle.clues) == len(puzzle.constraints)
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints

    result = Solver().solve(puzzle, stop_after=2)

    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment


def test_generated_four_item_puzzle_has_varied_visible_clue_types() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())

    assert len(puzzle.items) == 4
    assert len({clue.clue_type for clue in puzzle.clues}) >= 2


def test_seeded_generation_produces_deterministic_clue_types_and_text() -> None:
    template = create_template()

    first = PuzzleGenerator(random_source=random.Random(101)).generate(template)
    second = PuzzleGenerator(random_source=random.Random(101)).generate(template)

    assert [(clue.clue_type, clue.text) for clue in first.clues] == [
        (clue.clue_type, clue.text) for clue in second.clues
    ]


def test_every_generated_clue_constraint_matches_target_and_no_hidden_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(11)).generate(create_template())

    assert len(puzzle.clues) == len(puzzle.constraints)
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints
    assert all(clue.constraint.matches(puzzle.solution.assignment) for clue in puzzle.clues)


def test_generated_visible_puzzle_remains_uniquely_solvable_to_target() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(17)).generate(create_template())

    result = Solver().solve(puzzle, stop_after=2)

    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment


def test_multiple_seeded_four_item_puzzles_keep_visible_invariants_and_variety() -> None:
    adjacent_seen = False

    for seed in range(1, 16):
        puzzle = PuzzleGenerator(random_source=random.Random(seed)).generate(create_template())
        result = Solver().solve(puzzle, stop_after=2)

        assert result.has_unique_solution, seed
        assert result.solutions[0] == puzzle.solution.assignment
        assert len(puzzle.clues) == len(puzzle.constraints)
        assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints
        assert len({_visible_clue_meaning(clue) for clue in puzzle.clues}) >= 2

        adjacent_seen = adjacent_seen or any(
            isinstance(constraint, AdjacentConstraint) for constraint in puzzle.constraints
        )

    assert adjacent_seen


def test_quality_selection_improves_clue_type_variety(monkeypatch: pytest.MonkeyPatch) -> None:
    template = create_template()

    monkeypatch.setattr(puzzle_generator_module, "QUALITY_CANDIDATE_COUNT", 1)
    first_valid = PuzzleGenerator(random_source=random.Random(2)).generate(template)

    monkeypatch.setattr(puzzle_generator_module, "QUALITY_CANDIDATE_COUNT", 8)
    quality_selected = PuzzleGenerator(random_source=random.Random(2)).generate(template)

    first_variety = len({_visible_clue_meaning(clue) for clue in first_valid.clues})
    selected_variety = len({_visible_clue_meaning(clue) for clue in quality_selected.clues})

    assert selected_variety >= first_variety
    assert PuzzleGenerator()._quality_score(quality_selected) >= PuzzleGenerator()._quality_score(
        first_valid
    )


def test_generated_four_item_puzzles_use_multiple_clue_types_when_possible() -> None:
    for seed in range(1, 8):
        puzzle = PuzzleGenerator(random_source=random.Random(seed)).generate(create_template())

        assert len(puzzle.items) == 4
        assert len({_visible_clue_meaning(clue) for clue in puzzle.clues}) >= 2


def _visible_clue_meaning(clue: Clue) -> str:
    constraint = clue.constraint
    if isinstance(constraint, FixedPositionConstraint):
        if constraint.position.index == 1:
            return "far_left"
        return "far_right"

    return clue.clue_type.value


class AnchorDirectClueReducer:
    def reduce(self, puzzle: Puzzle) -> Puzzle:
        selected = [
            clue
            for clue in puzzle.clues
            if isinstance(
                clue.constraint,
                FixedPositionConstraint | DirectLeftOfConstraint | DirectRightOfConstraint,
            )
        ][:3]
        return Puzzle(
            items=puzzle.items,
            constraints=[clue.constraint for clue in selected],
            clues=selected,
            metadata=puzzle.metadata,
            solution=puzzle.solution,
        )


def test_difficulty_metadata_is_stored_after_clue_reduction_from_visible_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7), difficulty="medium").generate(create_template())

    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == 2
    assert _fixed_position_count(puzzle) == 1
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints

def test_generated_puzzle_metadata_difficulty_can_report_multiple_levels() -> None:
    default_puzzle = PuzzleGenerator(random_source=random.Random(1)).generate(create_template())
    anchored_puzzle = PuzzleGenerator(
        random_source=random.Random(1),
        clue_reducer=AnchorDirectClueReducer(),
        difficulty="easy",
    ).generate(create_template())

    assert default_puzzle.metadata is not None
    assert anchored_puzzle.metadata is not None
    difficulties = {default_puzzle.metadata.difficulty, anchored_puzzle.metadata.difficulty}
    assert difficulties <= {1, 2, 3}
    assert difficulties


def test_seeded_generation_is_deterministic_including_difficulty() -> None:
    template = create_template()

    first = PuzzleGenerator(random_source=random.Random(101)).generate(template)
    second = PuzzleGenerator(random_source=random.Random(101)).generate(template)

    assert first.metadata is not None
    assert second.metadata is not None
    assert first.metadata.difficulty == second.metadata.difficulty


def test_source_puzzle_metadata_is_copied_not_mutated() -> None:
    source = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    assert source.metadata is not None
    source.metadata.difficulty = 1

    generated = PuzzleGenerator(random_source=random.Random(8)).generate(source)

    assert generated.metadata is not None
    assert generated.metadata is not source.metadata
    assert source.metadata.difficulty == 1
    assert generated.metadata.difficulty in {1, 2, 3}


def _fixed_position_count(puzzle: Puzzle) -> int:
    return sum(isinstance(constraint, FixedPositionConstraint) for constraint in puzzle.constraints)


@pytest.mark.parametrize(
    ("difficulty", "expected_metadata", "expected_count"),
    [("easy", 1, 2), ("medium", 2, 1), ("hard", 3, 0)],
)
def test_requested_difficulty_controls_final_visible_fixed_position_count(
    difficulty: str, expected_metadata: int, expected_count: int
) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(1), difficulty=difficulty).generate(create_template())
    result = Solver().solve(puzzle, stop_after=2)

    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment
    assert len(puzzle.clues) == len(puzzle.constraints)
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints
    assert _fixed_position_count(puzzle) == expected_count
    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == expected_metadata


def test_typed_requested_difficulty_is_supported() -> None:
    from logical_puzzle_generator.generator import Difficulty

    puzzle = PuzzleGenerator(random_source=random.Random(2), difficulty=Difficulty.HARD).generate(create_template())

    assert _fixed_position_count(puzzle) == 0
    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == 3


def test_generation_retries_until_requested_difficulty_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    original = PuzzleGenerator._generate_candidate

    def mismatching_once(self: PuzzleGenerator, source, items, difficulty):
        nonlocal calls
        calls += 1
        if calls == 1:
            return None, "reduced puzzle has 2 visible FixedPositionConstraint clues, which does not match requested difficulty medium"
        return original(self, source, items, difficulty)

    monkeypatch.setattr(PuzzleGenerator, "_generate_candidate", mismatching_once)

    puzzle = PuzzleGenerator(random_source=random.Random(1), difficulty="medium", max_attempts=10).generate(create_template())

    assert calls >= 2
    assert _fixed_position_count(puzzle) == 1


def test_generation_raises_clear_error_when_no_matching_difficulty_can_be_generated() -> None:
    with pytest.raises(RuntimeError, match="Unable to generate a valid uniquely solvable easy puzzle"):
        PuzzleGenerator(
            random_source=random.Random(1),
            difficulty="easy",
            clue_reducer=EmptyClueReducer(),
            max_attempts=1,
        ).generate(create_template())


def test_omitted_difficulty_selects_random_valid_level() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(1)).generate(create_template())

    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty in {1, 2, 3}
    assert _fixed_position_count(puzzle) in {0, 1, 2}


def test_omitted_difficulty_selection_is_seeded_and_varies_across_seeds() -> None:
    first = PuzzleGenerator(random_source=random.Random(9)).generate(create_template())
    second = PuzzleGenerator(random_source=random.Random(9)).generate(create_template())
    selected_metadata: set[int] = set()

    assert first.metadata is not None
    assert second.metadata is not None
    assert first.metadata.difficulty == second.metadata.difficulty
    assert _fixed_position_count(first) == _fixed_position_count(second)

    for seed in range(1, 30):
        puzzle = PuzzleGenerator(random_source=random.Random(seed)).generate(create_template())
        assert puzzle.metadata is not None
        selected_metadata.add(puzzle.metadata.difficulty)

    assert selected_metadata == {1, 2, 3}


def _fixed_position_constraints(puzzle: Puzzle) -> list[FixedPositionConstraint]:
    return [
        constraint
        for constraint in puzzle.constraints
        if isinstance(constraint, FixedPositionConstraint)
    ]


def test_easy_fixed_position_clues_use_distinct_children_and_positions() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(12), difficulty="easy").generate(create_template())
    fixed_constraints = _fixed_position_constraints(puzzle)

    assert len(fixed_constraints) == 2
    assert len({constraint.item for constraint in fixed_constraints}) == len(fixed_constraints)
    assert len({constraint.position for constraint in fixed_constraints}) == len(fixed_constraints)
    assert all(constraint.matches(puzzle.solution.assignment) for constraint in fixed_constraints)


def test_medium_fixed_position_clue_selects_one_matching_child_position_fact() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(12), difficulty="medium").generate(create_template())
    fixed_constraints = _fixed_position_constraints(puzzle)

    assert len(fixed_constraints) == 1
    assert fixed_constraints[0].matches(puzzle.solution.assignment)


def test_fixed_position_selection_varies_children_and_positions_across_seeds() -> None:
    selected_children: set[str] = set()
    selected_positions: set[int] = set()

    for seed in range(1, 50):
        puzzle = PuzzleGenerator(random_source=random.Random(seed), difficulty="medium").generate(
            create_template()
        )
        fixed_constraints = _fixed_position_constraints(puzzle)
        assert len(fixed_constraints) == 1
        selected_children.add(fixed_constraints[0].item.name)
        selected_positions.add(fixed_constraints[0].position.index)

    assert selected_positions == {1, 2, 3, 4}
    assert {2, 3} <= selected_positions
    assert len(selected_children) > 1


def test_easy_fixed_position_selection_includes_middle_positions_across_seeds() -> None:
    selected_positions: set[int] = set()

    for seed in range(1, 50):
        puzzle = PuzzleGenerator(random_source=random.Random(seed), difficulty="easy").generate(
            create_template()
        )
        for constraint in _fixed_position_constraints(puzzle):
            selected_positions.add(constraint.position.index)
            assert constraint.matches(puzzle.solution.assignment)

    assert selected_positions == {1, 2, 3, 4}
    assert {2, 3} <= selected_positions


def test_hard_fixed_position_selection_never_retains_anchors() -> None:
    for seed in range(1, 20):
        puzzle = PuzzleGenerator(random_source=random.Random(seed), difficulty="hard").generate(
            create_template()
        )

        assert _fixed_position_constraints(puzzle) == []


def test_relational_derivation_never_introduces_extra_fixed_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(4), difficulty="easy").generate(create_template())
    generator = PuzzleGenerator(random_source=random.Random(4), difficulty="easy")

    relational_constraints = generator._derive_relational_constraints(puzzle.solution)

    assert relational_constraints
    assert not any(isinstance(constraint, FixedPositionConstraint) for constraint in relational_constraints)


def test_mandatory_fixed_anchors_survive_reduction() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(5), difficulty="easy").generate(create_template())

    assert len(_fixed_position_constraints(puzzle)) == 2
    assert all(
        clue.constraint in puzzle.constraints
        for clue in puzzle.clues
        if isinstance(clue.constraint, FixedPositionConstraint)
    )


def _relation_type_names(puzzle: Puzzle) -> set[str]:
    return {
        type(constraint).__name__
        for constraint in puzzle.constraints
        if not isinstance(constraint, FixedPositionConstraint)
    }


def test_generated_clue_sets_use_multiple_relation_types_when_possible() -> None:
    for difficulty in ("easy", "medium", "hard"):
        puzzle = PuzzleGenerator(random_source=random.Random(31), difficulty=difficulty).generate(create_template())
        assert len(_relation_type_names(puzzle)) >= 2


def test_identical_seeds_produce_identical_distributions() -> None:
    first = PuzzleGenerator(random_source=random.Random(42), difficulty="medium").generate(create_template())
    second = PuzzleGenerator(random_source=random.Random(42), difficulty="medium").generate(create_template())

    assert [type(constraint) for constraint in first.constraints] == [
        type(constraint) for constraint in second.constraints
    ]


def test_different_seeds_produce_different_distributions() -> None:
    distributions = {
        tuple(type(constraint).__name__ for constraint in PuzzleGenerator(
            random_source=random.Random(seed), difficulty="medium"
        ).generate(create_template()).constraints)
        for seed in range(40, 46)
    }

    assert len(distributions) > 1


def test_distribution_regression_over_100_puzzles_per_difficulty() -> None:
    supported_relations = {
        "DirectLeftOfConstraint",
        "LeftOfConstraint",
        "DirectRightOfConstraint",
        "RightOfConstraint",
        "AdjacentConstraint",
    }
    seen: set[str] = set()
    for difficulty in ("easy", "medium", "hard"):
        dominant_puzzles = 0
        for seed in range(100):
            puzzle = PuzzleGenerator(random_source=random.Random(seed), difficulty=difficulty).generate(create_template())
            relation_names = [
                type(constraint).__name__
                for constraint in puzzle.constraints
                if not isinstance(constraint, FixedPositionConstraint)
            ]
            seen.update(relation_names)
            if relation_names:
                most_common = max(relation_names.count(name) for name in set(relation_names))
                if most_common == len(relation_names) or most_common >= 4:
                    dominant_puzzles += 1
        assert dominant_puzzles < 10
    assert supported_relations <= seen

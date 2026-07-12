# AI Contribution Guide

This document defines the mandatory workflow for AI-assisted contributions.

## Required reading

Before modifying code or documentation, read:

1. `docs/01_AI_DEVELOPMENT_SPEC.md`
2. `docs/02_ARCHITECTURE.md`
3. `docs/03_CONTRIBUTING_AI.md`
4. `docs/04_ROADMAP.md`
5. `docs/05_DECISIONS.md`
6. Relevant source files and tests

## Development workflow

For every task:

1. Inspect the current implementation.
2. Identify the smallest safe change.
3. Preserve public APIs and documented architecture boundaries.
4. Update tests when behavior changes.
5. Update documentation in the same PR when behavior, commands, public APIs, localization text, or architecture descriptions change.
6. Run the relevant checks.
7. Create one focused commit.
8. Open a pull request describing the change and checks run.

## PR workflow

A pull request should include:

- a concise title with an appropriate prefix such as `docs:`, `fix:`, `feat:`, or `test:`;
- a summary of user-visible or maintainer-visible changes;
- test/check results;
- notes about any intentional limitations or deferred Version 2 work.

Do not mix unrelated feature, refactor, and documentation work in one PR.

## Review workflow

Reviewers and AI assistants should verify:

- tests pass;
- public APIs remain compatible unless a breaking change was requested;
- documentation examples match the actual code;
- language/localization behavior is documented when user-facing text changes, including deterministic clue wording templates;
- architecture documentation matches package responsibilities;
- ADRs are not contradicted;
- no placeholder implementations, dead prompts, or stale roadmap claims were introduced.

## Commit strategy

Use one logical commit per task. Preferred examples:

```text
docs: synchronize version 1.0 documentation
feat(generator): implement puzzle generation pipeline
fix(pdf): handle missing solution output path
test(generator): cover deterministic generation
```

Large work should be split into reviewable sub-commits that preserve a passing test suite.

## Documentation policy

Documentation is part of the product. Update it in the same PR when a change affects:

- installation or command examples;
- public APIs;
- package responsibilities;
- generator/PDF behavior, including child-friendly A4 lineup presentation;
- supported constraints or clue types;
- roadmap status;
- architectural decisions.

Version 1.0 documentation must describe the implemented repository, not planned work.

## Architecture preservation policy

Stable Version 1.0 boundaries:

- Solver and validator are the mathematical verification boundary.
- Constraints stay independent and expose `matches()` plus `description`.
- `PuzzleGenerator` owns orchestration and private constraint derivation.
- `ClueGenerator` only converts constraints to clues.
- `ClueReducer` removes human-readable clues and their corresponding constraints together when uniqueness remains true for the remaining visible constraints.
- PDF classes only render existing puzzle data.
- Themes supply template data only.

Do not redesign these boundaries without an explicit task and ADR update.

## Coding rules

Always:

- use type hints in new public code;
- keep classes and methods focused;
- prefer readable implementation over clever abstractions;
- follow the existing package structure;
- preserve backward-compatible wrappers unless removal is explicitly requested.

Never:

- introduce placeholder code or TODO implementations;
- duplicate core solver/generator logic;
- hide imports in `try`/`except` blocks;
- replace working subsystems for style-only reasons.

## Testing rules

Use pytest for behavior. Run formatting/type checks when relevant:

```bash
pytest
ruff check src tests
black --check src tests
mypy src
```

### Difficulty-policy guidance

Difficulty is owned by `DifficultyPolicy`: inspect only final visible constraints after clue reduction and count `FixedPositionConstraint` clues. Easy is exactly 2, Medium is exactly 1, Hard is 0. Version 1 four-player puzzles must always have exactly three visible clues: Easy has one relational clue, Medium has two, and Hard has three. `FixedPositionGenerator` constructs mandatory anchors and the target solution before relational constraints. Do not put difficulty logic in the solver, validator, clue renderer, PDF generator, or translation catalog.


## Constraint distribution policy

Keep clue-variety work in `ConstraintDistributionPolicy` and the generator/reducer orchestration. The policy may analyze, reject, and score existing constraints with neutral context such as `required_fixed_count`, but must not import or depend on `Difficulty`/`DifficultyPolicy`, classify difficulty, solve, validate uniqueness, translate, render PDFs, create target solutions, or add new clue/constraint types. Keep adjacent and non-adjacent relation semantics distinct: ordinary left/right generation requires distance >= 2, while direct and adjacent generation requires distance == 1. Use injected seeded randomness for equally valid relation choices and tied best subsets. Treat diversity as a rule-based quality preference; never weaken validator checks or the exact fixed-position difficulty rules owned by `DifficultyPolicy`.


## PDF presentation policy

PDF polish belongs in `src/logical_puzzle_generator/pdf/`, presentation/localization labels, PDF tests, and documentation. Do not change solver, validator, generator, clue generation, difficulty, clue counts, relation distribution, wording templates, or localization semantics for a presentation-only worksheet task. Puzzle and solution PDFs should remain layout-identical except that solution name boxes are filled from the existing solution assignment.

## Wording-template policy

When changing clue text, edit `TemplateCatalog` and presentation tests only unless the task explicitly changes mathematical semantics. Do not add wording logic to constraint classes, solver, validator, generator, difficulty policy, clue reducer, or PDF layout. New or changed German templates must use Swiss spelling and must not include `ß`. Template selection must use injected `random.Random` instances for deterministic seeded rendering.


## Relation-distribution regression guidance

Any generator, reducer, difficulty, or constraint-distribution change must keep the deterministic statistical gate passing. Run:

```bash
pytest tests/generator/test_relation_distribution_regression.py
```

The test uses the Tennis template with 200 Easy, 200 Medium, and 200 Hard puzzles from fixed integer seed ranges. It counts `DirectLeftOfConstraint`, `LeftOfConstraint`, `DirectRightOfConstraint`, `RightOfConstraint`, and `AdjacentConstraint`, and excludes `FixedPositionConstraint`. Do not loosen thresholds or skip the test to hide a regression; if a deliberate generation-policy change shifts the stable distribution, update the regression suite with deterministic evidence while keeping exact measured counts in test diagnostics rather than documentation. Ordinary non-direct left/right clues must remain meaningfully represented.

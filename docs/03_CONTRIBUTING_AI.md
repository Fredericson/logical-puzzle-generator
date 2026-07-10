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
- language/localization behavior is documented when user-facing text changes;
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
- generator/PDF behavior;
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

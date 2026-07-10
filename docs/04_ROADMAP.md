# Logical Puzzle Generator Roadmap

## Vision

Create an open-source logical puzzle generator capable of producing printable Einstein-style puzzles with exactly one unique solution while keeping the codebase simple, educational, and maintainable.

## Version 1.0 — Complete

Objective: deliver a command-line-capable Python package that generates and validates 4-item ordering puzzles and renders puzzle/solution PDFs.

Completed milestones:

- Domain model and package structure.
- Constraint hierarchy with far-left/far-right fixed-position, direct-left, left-of, direct-right, right-of, and adjacent next-to constraints.
- Brute-force solver, assignment iterator, solver result, statistics, and validator.
- Generator pipeline: `SolutionGenerator`, varied private constraint derivation, `ClueGenerator`, `ClueReducer`, `Validator`, and PDF generation.
- PDF output: `TextRenderer`, localized `ClueTextRenderer`, vector girl/lineup renderers, `PdfGenerator.create_puzzle_pdf()`, and `PdfGenerator.create_solution_pdf()` on A4 portrait pages.
- Tennis theme and `python -m logical_puzzle_generator.create_puzzle` entry point with `--language en` and `--language de`, including the German example `python -m logical_puzzle_generator.create_puzzle --number 3 --language de`.
- Version 1.0 documentation synchronization.
- Test coverage across engine, model, generator, and PDF packages.

Version 1.0 accepted limitations:

- Active puzzle solving uses one item category mapped to positions.
- The Tennis template includes extra thematic categories as template data, but multi-category logic is not solved in Version 1.0.
- Clue generation supports implemented Version 1.0 positional constraint classes only. PDF presentation supports English and German wording for those clue meanings.
- `Optimizer` is a compatibility boundary and does not alter puzzles.

## Version 2

Potential next release work:

- Multi-category puzzle relationships.
- Additional implemented constraints such as not-adjacent, between, and not-position.
- Richer clue generation from multiple categories.
- Puzzle-quality scoring remains intentionally simple and only compares candidates that already match the requested difficulty. Difficulty selection is implemented with the final visible fixed-position-count rule after clue reduction.
- More sophisticated clue minimization/optimization.
- JSON export and import.
- Batch generation.
- More example themes and committed sample outputs.
- Additional presentation languages beyond English and German.
- Packaging polish such as console scripts and published distributions.

## Future ideas

- Larger puzzle sizes such as 5×5.
- Puzzle packs.
- GUI or web application.
- REST API or cloud generation service.
- Additional illustration themes or layout customization.

## Commit 11.5 status

Completed: selectable difficulty. The CLI and public API accept easy, medium, and hard; generation retries until the final reduced uniquely solvable puzzle has the requested visible FixedPositionConstraint count.

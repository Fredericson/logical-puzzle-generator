# Logical Puzzle Generator Roadmap

## Vision

Create an open-source logical puzzle generator capable of producing printable Einstein-style puzzles with exactly one unique solution while keeping the codebase simple, educational, and maintainable.

## Version 1.0 — Complete

Objective: deliver a command-line-capable Python package that generates and validates 4-item ordering puzzles and renders puzzle/solution PDFs.

Completed milestones:

- Domain model and package structure.
- Constraint hierarchy with far-left/far-right fixed-position, direct-left, left-of, direct-right, right-of, and adjacent next-to constraints.
- Brute-force solver, assignment iterator, solver result, statistics, and validator.
- Generator pipeline: `SolutionGenerator`, varied private constraint derivation with distinct adjacent vs non-adjacent relation semantics, `ClueGenerator`, `ClueReducer`, `Validator`, and PDF generation.
- PDF output: `TextRenderer`, localized `ClueTextRenderer`, `TemplateCatalog`, vector girl/lineup renderers, polished child-facing worksheet layout, `PdfGenerator.create_puzzle_pdf()`, and `PdfGenerator.create_solution_pdf()` on A4 portrait pages.
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
- Puzzle-quality scoring remains intentionally simple and only compares candidates that already match the requested difficulty. Difficulty selection is implemented with the final visible direct-assignment rule for the active page task after clue reduction.
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

Completed: clue variety distribution policy with neutral fixed-count context, adjacent/non-adjacent relation semantic separation, rule-based early rejection of repetitive generated constraints, and seeded selection among tied best visible subsets that preserves diversity where possible.

Completed: selectable difficulty. The CLI and public API accept easy, medium, and hard; generation retries until the final uniquely solvable puzzle has the requested visible direct-assignment count. Position-only compatibility puzzles retain their established difficulty behavior; fixed-child Theme pages count canonical Theme direct-assignment identities while allowing the clue count needed for two-category solving.


## Commit 11.9 status

Completed: natural-language clue wording variations for all existing visible Version 1 constraint types. The implementation is presentation-only through `ClueTextRenderer` and `TemplateCatalog`; solver, validator, generator, clue reduction, difficulty, PDF layout, clue counts, and constraint semantics remain unchanged. Seeded renderers produce deterministic wording, and German templates keep Swiss spelling without `ß`.


## Commit 12.0 status

Completed: deterministic statistical CI regression coverage for visible relation distribution. The standard pytest suite samples 600 Tennis puzzles across fixed Easy/Medium/Hard seed ranges, verifies all five supported relation types occur within documented lower/upper bounds, keeps ordinary non-direct left/right clues represented, checks a 12-seed focused symptom regression, and confirms deterministic repeated counts.


## Commit 12.1 status

Completed: Version 1 child-facing PDF presentation polish. The worksheet now uses a calmer layout, balanced title metadata, more generous whitespace, larger writable lineup boxes, deterministic aligned vector geometry, and clearer clue numbering/wrapping. This was presentation-only; no generator behavior, clue wording, clue counts, relation distribution, difficulty classification, localization semantics, solver behavior, validator behavior, puzzle numbering semantics, or metadata changed.

## After Commit 12.2

Commit 12.2 implements multiple available category definitions per theme and one selected category instance per generated puzzle page. Still deferred: multiple category pages in one generated PDF, more than one active thematic category in a single puzzle page, PuzzleBook orchestration, summary rendering, configurable/random names, gender selection, comic animal protagonists, category repetition scheduling, batch generation, numeric categories such as future tournament wins, and larger 5×5 puzzles.

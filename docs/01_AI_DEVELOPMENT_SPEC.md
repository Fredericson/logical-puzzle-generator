# AI Development Specification

## Logical Puzzle Generator v1.0

This document is the authoritative implementation specification for continuing development after the Version 1.0 documentation release. It describes the current repository, not an aspirational design.

## 1. Project goal

Build a Python application that automatically generates printable Einstein-style logic puzzles with exactly one unique solution.

Version 1.0 focuses on 4-item ordering puzzles. The active generated solution maps items from a single source category to ordered positions. The built-in Tennis template contains additional thematic categories, but Version 1.0 uses the first category (`players`) as the permutation source.

## 2. Current project status

Version 1.0 is complete.

Completed capabilities:

- Domain model: `Item`, `Position`, `Category`, `Metadata`, `Clue`, `Puzzle`, and `Solution`.
- Constraint model: fixed position, left-of, right-of, and adjacent constraints.
- Brute-force engine: assignment iteration, solver result, statistics, validator, and optimizer compatibility class.
- Generator package: `SolutionGenerator`, `ClueGenerator`, `ClueReducer`, `PuzzleGenerator`, and `PuzzleTemplate`.
- Internal constraint derivation inside `PuzzleGenerator`.
- PDF package: `TextRenderer`, `GirlFigureRenderer`, `PlayerLineupRenderer`, and `PdfGenerator` for child-friendly A4 puzzle and solution PDFs.
- Localization: `Language`, `TranslationCatalog`, `TemplateCatalog`, and `ClueTextRenderer` for deterministic English/German presentation text variations.
- Tennis theme and `create_puzzle` entry point.
- Pytest coverage for engine, generator, model, and PDF behavior.

## 3. Package layout

```text
src/logical_puzzle_generator/
  model/
  constraints/
  engine/
  generator/
  pdf/
  localization.py
  clue_text_renderer.py
  themes/
  create_puzzle.py
```

The architecture is stable. Extend it carefully; do not redesign it without an accepted ADR.

## 4. Functional requirements

The application shall:

- generate a random valid item-to-position solution;
- derive mathematical constraints from that solution;
- generate human-readable clues from supported constraints;
- assemble a `Puzzle` containing items, constraints, clues, metadata, and solution;
- validate that the puzzle has exactly one solution;
- reduce visible clues and their corresponding constraints together while preserving items, metadata, and solution;
- validate uniqueness only against the remaining visible constraints;
- forbid hidden constraints that are not represented by visible clues;
- export a printable A4 portrait puzzle PDF in English or German with localized headings and clues;
- show the four-player Tennis puzzle as four anonymous vector girl placeholders in left-to-right position order, with one empty writable name box under each figure and a separate available-names list;
- export a printable A4 portrait solution PDF in English or German using the same lineup with names filled from `puzzle.solution.assignment` in position order.

## 5. Generator pipeline

```text
Source template, puzzle, or iterable of Item
        ↓
Select requested/random Difficulty
        ↓
FixedPositionGenerator.generate(items, difficulty)
        ↓
Target Solution + mandatory FixedPositionConstraint anchors
        ↓
PuzzleGenerator._derive_relational_constraints(solution)
        ↓
ConstraintDistributionPolicy accepts/scores fixed + relational constraints using neutral required_fixed_count context

ClueGenerator.generate(fixed + relational constraints)
        ↓
Puzzle assembly
        ↓
Validator.has_unique_solution(puzzle)
        ↓
ClueReducer.reduce(puzzle, difficulty) preserving exact fixed count
        ↓
Validator.has_unique_solution(reduced)
        ↓
DifficultyPolicy match/classify
        ↓
Return Puzzle or retry until max_attempts is exhausted
```

Version 1.0 intentionally has no public `ConstraintGenerator`. Constraint derivation is a private `PuzzleGenerator` responsibility.

## 6. Supported constraint and clue types

Implemented constraints:

- `FixedPositionConstraint`
- `DirectLeftOfConstraint`
- `LeftOfConstraint`
- `DirectRightOfConstraint`
- `RightOfConstraint`
- `AdjacentConstraint`

`ConstraintDistributionPolicy` may reject repetitive generated distributions before clue creation and scores acceptable distributions deterministically. It receives neutral context such as `required_fixed_count`; it must not import or depend on `Difficulty` or `DifficultyPolicy`, classify difficulty, solve, validate uniqueness, or affect the supported type list. Every visible `Clue` owns exactly one `Constraint`. `ClueGenerator` supports exactly those constraint classes, and `ClueReducer` removes a `Clue` and its corresponding `Constraint` together. Uniqueness is validated only against the remaining visible constraints; hidden constraints are forbidden. `ClueType` also contains reserved values (`NOT_ADJACENT`, `BETWEEN`, and `NOT_POSITION`) for compatibility/future expansion; they are not generated by Version 1.0.

## 7. Solver rules

- Keep the brute-force implementation.
- Preserve `stop_after` early exit behavior.
- Preserve deterministic results for a fixed item order and fixed random seed.
- Keep solver and validator independent of generator, PDF, themes, and UI.

## 8. Language and PDF requirements

English (`en`) is the default presentation language. German (`de`) is first-class for the CLI, `create_puzzle(..., language=...)`, and `PdfGenerator(language=...)`. User-facing PDF headings, labels, solution headings, solving-grid labels, and localized clue wording belong in the localization/presentation layer, not in constraints, solver, validator, or generator logic. Unsupported language values must be rejected clearly.

## 9. PDF requirements

Puzzle PDF:

- title, theme, and optional difficulty metadata rendered with localized child-friendly labels;
- numbered clues;
- empty solving grid;
- item list.

Solution PDF:

- title, theme, and optional difficulty metadata rendered with localized child-friendly labels;
- completed position-to-item solution table;
- original clue list.

PDF generation is presentation-only and must not perform solving or generation. Difficulty values remain numeric in `Metadata`; the PDF/localization layer maps those numbers to child-friendly labels for display only and omits the difficulty line when no value is present.

## 10. Coding standards

- Python 3.11+.
- Type hints for public interfaces and new code.
- Dataclasses for simple domain models where appropriate.
- Immutable/frozen domain objects where already established.
- Small focused classes.
- No global mutable generation state.
- Readable code over clever code.

## 11. Testing

Use pytest.

Required checks for generator/PDF changes:

- puzzle generation succeeds;
- generated puzzle has exactly one solution;
- generated clues are valid `Clue` instances with text;
- deterministic behavior when a seeded `random.Random` is supplied;
- PDF output files can be written for puzzle and solution PDFs;
- localized rendering preserves puzzle immutability, clue/constraint one-to-one mapping, and seeded generation determinism.

## 12. AI development rules

Mandatory rules:

- Preserve public APIs unless a task explicitly authorizes a breaking change.
- Implement one logical commit at a time.
- Keep backward compatibility wrappers such as `PdfGenerator.create()` and legacy `PuzzleGenerator` dependency arguments.
- Follow existing package boundaries.
- Update documentation in the same change when behavior, commands, or public APIs change.

Do not:

- redesign the architecture;
- replace the solver, assignment model, validator, or constraint hierarchy;
- introduce placeholder implementations;
- add TODO-driven code;
- invent requirements not present in the task or roadmap.

## 13. Definition of done

A change is complete when:

- tests pass;
- examples in documentation match the current public API;
- architecture documentation matches the code;
- ADRs do not contradict implementation;
- public API compatibility is preserved or explicitly documented;
- one focused commit and pull request are prepared.

## 11. Commit 11.3 PDF presentation requirement

The current Tennis PDF presentation is child-facing rather than a technical solving table. The PDF layer draws anonymous girl figures directly with ReportLab vector primitives and must not depend on external images, URLs, or downloads. Position 1 is the far-left lineup slot, position 4 is the far-right slot, and neighbouring slots represent adjacent positions. Puzzle PDFs leave all name boxes empty; solution PDFs fill those boxes from the existing `Puzzle.solution.assignment` only. This remains presentation-only and must not change generation, solving, validation, clue semantics, difficulty, or puzzle numbering.


## 12. Commit 11.4 difficulty label requirement

Puzzle difficulty remains numeric internal metadata, calculated from final visible constraint semantics after clue reduction. Child-facing puzzle and solution PDFs must never render that raw number; they render localized presentation labels instead (`Easy`, `Medium`, `Hard` in English and `Leicht`, `Mittel`, `Schwierig` in German). The mapping belongs only in the localization/presentation layer and must not change solver, validator, generator, constraints, clue reduction, metadata storage, puzzle numbering, or lineup geometry.

## 13. Commit 11.5 difficulty estimation requirement

Difficulty is calculated after clue reduction from final visible constraints only by counting `FixedPositionConstraint` clues: Easy has exactly two, Medium exactly one, and Hard zero. Direct left/right, adjacent, left-of, and right-of constraints do not count. Version 1 four-player puzzles always contain exactly three visible clues: Easy has two fixed-position clues plus one relational clue, Medium has one fixed-position clue plus two relational clues, and Hard has three relational clues. PDF localization remains presentation-only and maps stored numeric difficulty values to localized labels.


## Clue diversity quality goals

Constraint distribution is a soft, rule-based quality optimization. The generator should prefer varied mixes of the existing fixed-position, direct-left, left-of, direct-right, right-of, and adjacent constraints, while avoiding distributions dominated by one relation type. The comparison score is intentionally small and deterministic: it prioritizes distinct relation types, penalizes repeated/dominant relation types, and uses adjacency/direct-neighbour presence as minor tie-breakers. `DifficultyPolicy` remains the sole difficulty owner; displayed difficulty still derives from final visible fixed-position counts plus unique-solution validation.


## 12. Presentation wording templates

`TemplateCatalog` is the central source for localized clue sentence templates. It stores multiple equivalent named-placeholder templates for every visible Version 1 constraint type: fixed position, direct-left, left-of, direct-right, right-of, and adjacent. `ClueTextRenderer` chooses one template per clue with the injected `random.Random` source and substitutes semantic roles such as `{A}`, `{B}`, and `{position}`. This preserves deterministic output for identical seeds without changing solver, validator, generator, clue reduction, difficulty, or PDF layout logic.

Constraints remain language-independent and continue to define only mathematical semantics through `matches(assignment)`. German wording follows Swiss spelling and never uses `ß`.

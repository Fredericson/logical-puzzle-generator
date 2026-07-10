# Architecture Decision Records

This document records accepted architectural decisions for Version 1.0.

## ADR-001: Use Python

Status: Accepted

Decision: implement the project in Python.

Reason: Python is readable, easy to test, and approachable for contributors.

## ADR-002: Keep a package-oriented architecture

Status: Accepted

Decision: separate responsibilities into `model`, `constraints`, `engine`, `generator`, `pdf`, and `themes` packages.

Reason: clear package boundaries make the repository easier to maintain and reduce accidental coupling.

## ADR-003: Use brute-force solving for Version 1.0

Status: Accepted

Decision: keep the solver as a straightforward brute-force permutation checker with optional early exit.

Reason: Version 1.0 targets four active items, where brute force is simple, deterministic, and fast enough.

## ADR-004: Represent domain concepts explicitly

Status: Accepted

Decision: use explicit objects such as `Item`, `Position`, `Category`, `Puzzle`, `Clue`, and `Solution` rather than passing primitive strings and dictionaries everywhere.

Reason: explicit domain models improve readability and make public APIs easier to understand.

## ADR-005: Keep constraints independent

Status: Accepted

Decision: each constraint implements `matches(assignment)` and exposes `description` without depending on other constraints.

Reason: independent constraints keep the solver generic and make clue conversion straightforward.

## ADR-006: Separate solver, generator, and PDF rendering

Status: Accepted

Decision: the solver validates puzzles, the generator creates puzzles, and the PDF package renders existing puzzle data.

Reason: keeping these responsibilities separate prevents presentation or generation details from leaking into mathematical verification.

## ADR-007: Preserve stable architecture boundaries

Status: Accepted

Decision: future work should extend the current boundaries instead of replacing the solver, validator, assignment model, constraint hierarchy, or generator orchestration without an explicit ADR.

Reason: predictable boundaries help human and AI contributors make safe incremental changes.

## ADR-008: Prefer complete implementations over placeholders

Status: Accepted

Decision: do not merge placeholder code, mock implementations, or TODO-driven behavior.

Reason: incomplete code obscures repository status and slows future development.

## ADR-009: Make `PuzzleGenerator` the Version 1.0 orchestration boundary

Status: Accepted

Decision: `PuzzleGenerator` coordinates solution generation, private constraint derivation, clue generation, uniqueness validation, clue reduction, final validation, retry handling, and clear generation failure messages.

Reason: this keeps robustness checks in one orchestration boundary while reusing `SolutionGenerator`, `ClueGenerator`, `ClueReducer`, and `Validator`.

## ADR-010: Keep constraint derivation internal for Version 1.0

Status: Accepted

Decision: do not expose a public `ConstraintGenerator` in Version 1.0. Constraint derivation remains a private `PuzzleGenerator` implementation detail.

Reason: the current derivation is intentionally narrow and tied to the Version 1.0 ordering-puzzle pipeline. A public abstraction would imply extension points that are not yet stable.

## ADR-011: Treat PDF generation as presentation-only

Status: Accepted

Decision: `TextRenderer` and `PdfGenerator` render existing puzzles and must not solve, generate, or mutate puzzle logic.

Reason: this preserves a clean dependency direction and keeps PDF behavior testable independently from generation.


## ADR-012: Visible clues and constraints remain one-to-one

Status: Accepted

Decision:

- Every visible clue owns exactly one `Constraint`.
- `ClueReducer` removes a `Clue` and its corresponding `Constraint` together.
- `Validator` validates only visible constraints.
- Hidden constraints are forbidden.
- Direct-left and direct-right relationships are explicit constraint types.
- Fixed-position endpoint clues render as "far left" and "far right".

Rationale: puzzles must not appear ambiguous to the player while remaining unique internally. The visible clue set and the mathematical constraint set therefore stay aligned throughout generation, reduction, validation, and PDF rendering.


## ADR-013: Select the highest-quality valid generated candidate

Status: Accepted

Decision: `PuzzleGenerator` generates multiple valid candidate puzzles when possible, validates unique solvability before and after clue reduction, scores the reduced visible clue sets with a deterministic quality heuristic, and returns the highest-scoring candidate.

The internal quality score rewards varied clue meanings, endpoint clues, adjacent clues, direct-left/direct-right clues, and balanced clue distributions. It penalizes duplicate clue meanings and candidates dominated by one clue meaning. Scoring is based on constraint type and `ClueType`, not rendered clue text, so it remains independent from localisation and PDF wording. Candidate count is controlled by the internal `QUALITY_CANDIDATE_COUNT` constant rather than by a new public API.

Rationale: Version 1.0 already guarantees mathematical correctness and unique solvability. Human-facing quality improves when the generator can compare several valid alternatives instead of returning the first valid puzzle. Keeping the selection stage inside `PuzzleGenerator` preserves the existing Solver, Validator, ClueReducer, PDF, and public API boundaries while maintaining deterministic output for seeded random sources.


## ADR-014: Keep localization in the presentation layer

Status: Accepted

Decision: support English and German through a small internal `Language` abstraction, `TranslationCatalog`, and `ClueTextRenderer`. Constraints, solver, validator, and generator remain language-independent. English clue text stored on `Clue` remains backward compatible; localized PDF clue wording is rendered from the clue's one-to-one constraint in the presentation layer.

Rationale: localization changes how a puzzle is presented, not what mathematical constraints mean or how puzzles are generated and validated. Centralizing translated labels and clue wording avoids scattered language checks while preserving existing architecture boundaries.


## ADR-015: Render the Tennis PDF as a reusable vector lineup

Status: Accepted

Decision: replace the technical vertical solving table in generated PDFs with an A4 portrait, child-friendly horizontal lineup for the four-player Tennis puzzle. The PDF package owns `GirlFigureRenderer` for anonymous ReportLab vector figures and `PlayerLineupRenderer` for left-to-right position slots, writable boxes, and optional solved labels.

Rationale: the puzzle is intended to be understood visually by children. Keeping illustrations and lineup geometry in focused PDF components preserves the presentation-only boundary: generator, solver, validator, constraints, language semantics, difficulty, and numbering remain unchanged. The solution PDF can safely share the same layout by receiving labels derived from `puzzle.solution.assignment` rather than solving again. Difficulty remains numeric metadata classified by the generator from final visible fixed-position clues; localized child-facing difficulty labels are provided by the presentation/localization layer for both puzzle and solution PDFs.

## ADR-016: Superseded heuristic difficulty estimate

Decision: superseded by ADR-017. The old score-based difficulty heuristic is no longer the authoritative difficulty definition.

Rationale: child-facing difficulty should describe the puzzle the player actually receives. Removed clues, hidden/original constraints, rendered wording, PDF language, and the target solution must not shortcut the estimate.

Current rule: see ADR-017. Only the count of final visible `FixedPositionConstraint` clues matters.

Consequences: future generated clue/constraint types must define their difficulty impact before they are made visible. PDF localization remains presentation-only: `TranslationCatalog` maps stored numeric values to English/German labels and does not estimate difficulty.

## ADR-017: Select difficulty by visible fixed-position clue count

Decision: ADR-016 is superseded for Version 1 difficulty classification. `DifficultyPolicy` is the authoritative classifier and inspects only the final reduced puzzle constraints that correspond one-to-one with visible clues. Easy means exactly two visible `FixedPositionConstraint` clues, Medium means exactly one, and Hard means zero. Direct-left, direct-right, adjacent, left-of, and right-of constraints are not fixed-position clues and never count as anchors. For four-player puzzles, Version 1 always exposes exactly three visible clues: Easy adds one relational clue, Medium adds two, and Hard adds three.

Rationale: the previous heuristic often labelled puzzles Medium even when they were too difficult for the intended child. A fixed-position-count rule is predictable, testable, independent of language/PDF text, and based on the puzzle the child actually sees.

Consequences: `PuzzleGenerator` accepts an optional requested difficulty (omitted/`None` chooses randomly with the injected random source), delegates mandatory fixed assignment and target solution construction to `FixedPositionGenerator`, derives relational constraints separately, selects only the required four-player relational clue count before clue rendering whenever possible, reduces clues and constraints together while preserving the exact fixed count, validates unique solvability, classifies the final visible constraints, and retries until a matching candidate is found or raises a clear `RuntimeError` after `max_attempts`. Numeric metadata remains `1` Easy, `2` Medium, and `3` Hard. PDF and translation components render stored metadata only and do not recalculate difficulty.


## ADR-018: Use a deterministic constraint distribution policy for clue variety

Decision: `ConstraintDistributionPolicy` analyzes generated fixed and relational constraints before clue generation, rejects clearly poor type distributions with neutral context such as `required_fixed_count`, and scores acceptable distributions for quality selection and reducer tie-breaking. It uses only the existing Version 1 constraint types, deterministic rule checks, and a small tuple score based on relation-type variety, repeats, dominance, adjacency, and direct-neighbour presence.

Rationale: uniqueness and difficulty rules make puzzles correct, but balanced clue types make them more enjoyable. Keeping distribution scoring separate preserves Solver, Validator, FixedPositionGenerator, ClueGenerator, ClueReducer, DifficultyPolicy, and PdfGenerator responsibilities. The policy deliberately does not import or depend on `Difficulty` or `DifficultyPolicy`; those remain the only difficulty-classification boundary.

Consequences: clue diversity can improve without changing mathematical correctness. Poor distributions are retried before expensive later stages, while final visible puzzles are still validated for unique solvability and exact requested difficulty. ADR-017 remains unchanged: difficulty is still classified only by final visible `FixedPositionConstraint` count.

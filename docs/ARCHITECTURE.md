# ARCHITECTURE.md

# Logical Puzzle Generator -- Architecture Guide

> This document describes the intended architecture of the Logical
> Puzzle Generator. It is intended for developers and AI coding
> assistants.

------------------------------------------------------------------------

# 1. Vision

The project generates Einstein-style logical puzzles completely
automatically.

Pipeline:

``` text
Random Solution
      ↓
Constraint Generation
      ↓
Human Readable Clues
      ↓
Puzzle Assembly
      ↓
Uniqueness Validation
      ↓
Puzzle PDF
      ↓
Solution PDF
```

Only puzzles with exactly one solution are accepted.

------------------------------------------------------------------------

# 2. Design Principles

-   Small, focused classes
-   Single Responsibility Principle
-   Composition over inheritance
-   Immutable domain objects where appropriate
-   Clear package boundaries
-   Deterministic behaviour when seeded
-   Readability over cleverness

------------------------------------------------------------------------

# 3. Package Overview

``` text
logical_puzzle_generator/

model/
constraints/
engine/
generator/
pdf/
themes/
tests/
```

## model

Pure domain objects.

Contains:

-   Puzzle
-   Solution
-   Assignment
-   Item
-   Position
-   Category
-   Metadata
-   Clue
-   ClueType

Rules:

-   No business logic
-   Mostly dataclasses
-   Prefer immutable objects

------------------------------------------------------------------------

## constraints

Represents logical rules.

Each constraint must:

-   inherit Constraint
-   implement matches()
-   expose description

Constraints must never know each other.

------------------------------------------------------------------------

## engine

Mathematical core.

Responsibilities:

-   enumerate assignments
-   validate constraints
-   determine uniqueness
-   collect statistics

The engine must never know anything about PDF, themes or UI.

------------------------------------------------------------------------

## generator

Responsible for creating puzzles.

Classes:

SolutionGenerator Creates random candidate solutions.

ClueGenerator Converts a solution into logical constraints and human
readable clues.

PuzzleGenerator Coordinates the complete generation pipeline.

Pseudo flow:

``` python
while True:
    solution = SolutionGenerator().generate()
    clues = ClueGenerator().generate(solution)
    puzzle = Puzzle(...)
    if Validator().has_unique_solution(puzzle):
        return puzzle
```

------------------------------------------------------------------------

## pdf

Responsible only for rendering.

Never contains puzzle logic.

Outputs:

-   Puzzle PDF
-   Solution PDF

------------------------------------------------------------------------

## themes

Provides reusable content.

Examples:

-   Tennis
-   Animals
-   School
-   Space

A theme supplies names and categories. It never contains solver logic.

------------------------------------------------------------------------

# 4. Data Flow

``` text
Theme
   ↓
SolutionGenerator
   ↓
Solution
   ↓
ClueGenerator
   ↓
Constraint + Clue
   ↓
Puzzle
   ↓
Validator
   ↓
Solver
   ↓
Unique?
   ↓
PDF
```

------------------------------------------------------------------------

# 5. Solver Architecture

The solver is intentionally brute force.

Reasons:

-   Simple
-   Reliable
-   Easy to test
-   Sufficient for 4×4 puzzles

Future optimisation must preserve the public API.

------------------------------------------------------------------------

# 6. Constraint Philosophy

Constraints are independent.

Examples:

-   LeftOf
-   RightOf
-   Adjacent
-   FixedPosition
-   NotAdjacent
-   NotPosition

A constraint answers only:

``` python
constraint.matches(assignment)
```

Nothing else.

------------------------------------------------------------------------

# 7. Generator Philosophy

The generator must never guess.

Preferred algorithm:

1.  Create random solution.
2.  Derive valid constraints.
3.  Convert constraints into clues.
4.  Assemble puzzle.
5.  Validate uniqueness.
6.  Retry if necessary.

------------------------------------------------------------------------

# 8. Coding Standards

Python 3.13

Requirements:

-   type hints
-   dataclasses
-   slots=True
-   small classes
-   descriptive names
-   pytest
-   no global state

------------------------------------------------------------------------

# 9. Stability Rules

The following components are considered stable.

DO NOT redesign:

-   Assignment
-   Solver
-   Validator
-   Constraint hierarchy
-   Repository structure

Only extend functionality.

------------------------------------------------------------------------

# 10. Version Roadmap

## Version 1.0

-   4×4 puzzles
-   PDF output
-   Tennis theme

## Version 2.0

-   5×5 puzzles
-   Better optimisation
-   Difficulty estimation

## Version 3.0

-   Additional themes
-   JSON export
-   Batch generation

------------------------------------------------------------------------

# 11. Definition of Success

The project is complete when:

``` python
generator = PuzzleGenerator()

puzzle = generator.generate()
```

produces

-   one valid puzzle
-   exactly one solution
-   puzzle PDF
-   solution PDF

without manual intervention.

------------------------------------------------------------------------

# 12. Guidance for AI Assistants

Before making changes:

1.  Read AI_DEVELOPMENT_SPEC.md.
2.  Read this file completely.
3.  Read the repository.
4.  Preserve the architecture.
5.  Implement one commit at a time.
6.  Return complete files only.
7.  Avoid placeholders and TODOs.

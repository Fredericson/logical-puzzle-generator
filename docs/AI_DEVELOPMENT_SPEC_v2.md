# AI Development Specification

## Logical Puzzle Generator v1.0

> **Purpose**
>
> This document is the authoritative specification for continuing the
> development of the *Logical Puzzle Generator*. It is written so that
> any capable AI coding assistant (GPT, Claude, Gemini, Cursor, Copilot,
> etc.) can continue development without requiring the original
> conversation.

------------------------------------------------------------------------

# 1. Project Goal

Build a Python application that automatically generates printable
Einstein-style logical puzzles with **exactly one unique solution**.

Version 1.0 focuses on a **4×4 puzzle generator**.

The project is intended to be open source and easy to extend.

------------------------------------------------------------------------

# 2. Current Project Status

## Completed (Commits 1--9)

-   Project structure
-   Domain model
-   Assignment
-   Assignment iterator
-   Solver
-   Solver statistics
-   Solver result
-   Validator
-   Optimizer
-   Constraint hierarchy
-   Core constraint implementations
-   Tests (partial)

## Remaining

### Commit 10

-   Generator
    -   SolutionGenerator
    -   ClueGenerator
    -   PuzzleGenerator

### Commit 11

-   PDF generation
-   Solution PDF

### Commit 12

-   Tennis theme
-   Example puzzles

### Commit 13

-   Documentation
-   Examples
-   Additional tests
-   Release preparation

------------------------------------------------------------------------

# 3. Architecture

    src/
        logical_puzzle_generator/
            model/
            constraints/
            engine/
            generator/
            pdf/
            themes/
            tests/

The architecture is considered stable.

**Extend the project. Do not redesign it.**

------------------------------------------------------------------------

# 4. Functional Requirements

The application shall:

-   generate a random puzzle
-   generate clues
-   guarantee exactly one solution
-   export a printable puzzle
-   export the solution

------------------------------------------------------------------------

# 5. Generator Pipeline

    Generate Solution
            ↓
    Generate Constraints
            ↓
    Generate Clues
            ↓
    Build Puzzle
            ↓
    Validate uniqueness
            ↓
    Return Puzzle

Pseudo code:

``` python
while True:
    solution = SolutionGenerator().generate()
    clues = ClueGenerator().generate(solution)
    puzzle = Puzzle(...)
    if Validator().has_unique_solution(puzzle):
        return puzzle
```

------------------------------------------------------------------------

# 6. Supported Constraint Types

Version 1.0

-   Fixed Position
-   Left Of
-   Right Of
-   Adjacent
-   Not Adjacent
-   Not Position

------------------------------------------------------------------------

# 7. Solver Rules

-   Keep brute-force implementation
-   Support early exit
-   Keep deterministic behaviour
-   No redesign

------------------------------------------------------------------------

# 8. PDF Requirements

Puzzle PDF

-   title
-   theme
-   clues
-   empty solving grid

Solution PDF

-   completed grid

------------------------------------------------------------------------

# 9. Coding Standards

-   Python 3.13
-   dataclasses
-   slots=True
-   type hints everywhere
-   immutable model where appropriate
-   small focused classes
-   no global state
-   readable code over clever code

------------------------------------------------------------------------

# 10. Testing

Use pytest.

Every generator component must have tests.

Acceptance:

-   puzzle has at least one solution
-   puzzle has exactly one solution
-   generated clues are valid
-   deterministic behaviour when seeded

------------------------------------------------------------------------

# 11. AI Development Rules

These rules are mandatory.

## DO NOT

-   redesign the architecture
-   replace the solver
-   replace Assignment
-   replace Validator
-   replace Constraint hierarchy
-   rename packages unnecessarily
-   introduce TODO implementations
-   introduce placeholder code
-   create mock implementations

## ALWAYS

-   preserve public APIs
-   implement one commit at a time
-   return complete files
-   keep backward compatibility
-   follow existing coding style
-   use existing domain model

------------------------------------------------------------------------

# 12. Definition of Done

Version 1.0 is complete when the following works:

``` python
from logical_puzzle_generator.generator import PuzzleGenerator

generator = PuzzleGenerator()

puzzle = generator.generate()
```

and

-   Validator confirms exactly one solution
-   Puzzle PDF is generated
-   Solution PDF is generated

without manual intervention.

------------------------------------------------------------------------

# 13. Long-Term Roadmap

Version 2.0

-   5×5 puzzles
-   difficulty estimation
-   optimisation
-   JSON export

Version 3.0

-   multiple themes
-   multilingual support
-   batch generation
-   puzzle packs

------------------------------------------------------------------------

# 14. Recommended AI Prompt

    Read the complete repository.

    Read AI_DEVELOPMENT_SPEC.md first.

    Do not redesign the project.

    Implement exactly one commit.

    Return complete files only.

    No placeholders.
    No TODOs.
    No mock implementations.

    Keep the existing architecture.

------------------------------------------------------------------------

# 15. Success Criteria

A child should be able to receive a newly generated logical puzzle,
solve it on paper, and verify the unique solution using the generated
solution PDF.

The project should remain clean, maintainable and easily extensible.

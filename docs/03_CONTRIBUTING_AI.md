# CONTRIBUTING_AI.md

# AI Contribution Guide

> This document defines the mandatory workflow for any AI assistant
> contributing to the Logical Puzzle Generator project.

------------------------------------------------------------------------

# Purpose

Ensure that every AI contributes consistently, preserves the
architecture, and produces production-quality code.

------------------------------------------------------------------------

# Project Goals

The primary goal is **not** to build the most advanced puzzle generator.

The primary goal is to deliver Version 1.0:

-   Automatic 4×4 puzzle generation
-   Exactly one unique solution
-   Printable puzzle PDF
-   Printable solution PDF

------------------------------------------------------------------------

# Required Reading

Before writing any code:

1.  Read `docs/AI_DEVELOPMENT_SPEC.md`
2.  Read `docs/ARCHITECTURE.md`
3.  Read the complete repository
4.  Understand the current implementation

Do not start coding before understanding the project.

------------------------------------------------------------------------

# Development Workflow

For every task:

1.  Analyse the existing implementation.
2.  Produce a short implementation plan.
3.  Modify the minimum number of files.
4.  Keep backward compatibility.
5.  Ensure tests still pass.
6.  Produce one logical commit.

------------------------------------------------------------------------

# Commit Rules

One feature per commit.

Preferred commit format:

    feat(generator): implement puzzle generation pipeline
    fix(pdf): correct layout
    refactor(engine): improve solver performance
    test(generator): add generator tests
    docs: update architecture
--------------------------------------------------------------------------

# Commit Policy

Large features must be split into reviewable sub-commits.

Example:

Commit 10.1
Core model restoration

Commit 10.2
Solution generation

Commit 10.3
Clue generation

Commit 10.4
Pipeline integration

------------------------------------------------------------------------

# Coding Rules

Always:

-   use Python type hints
-   use dataclasses where appropriate
-   prefer immutable models
-   keep classes small
-   keep methods focused
-   write readable code
-   follow the existing package structure

Never:

-   introduce placeholder code
-   commit TODO implementations
-   duplicate logic
-   redesign working components

------------------------------------------------------------------------

# Architecture Rules

The following components are considered stable:

-   Solver
-   Validator
-   Assignment
-   Constraint hierarchy
-   Repository structure

Extend them only when absolutely necessary.

------------------------------------------------------------------------

# Generator Rules

The generator shall:

1.  Create a candidate solution.
2.  Derive valid constraints.
3.  Generate human-readable clues.
4.  Assemble a puzzle.
5.  Validate uniqueness.
6.  Retry if necessary.

------------------------------------------------------------------------

# Testing Rules

Every new feature must include tests.

Required checks:

-   Puzzle generation succeeds
-   Exactly one solution exists
-   Generated clues are valid
-   Deterministic behaviour with fixed random seed

------------------------------------------------------------------------

# Pull Request Checklist

Before considering work complete:

-   [ ] Code builds
-   [ ] Tests pass
-   [ ] Public APIs preserved
-   [ ] No placeholder code
-   [ ] Documentation updated
-   [ ] Commit message follows conventions

------------------------------------------------------------------------

# AI Behaviour

The AI should:

-   preserve architecture
-   avoid unnecessary refactoring
-   return complete files
-   prefer small, reviewable commits
-   explain design decisions briefly

The AI should not:

-   invent missing requirements
-   replace existing subsystems
-   optimise prematurely
-   ignore the specification

------------------------------------------------------------------------

# Definition of Success

A successful contribution moves the project closer to Version 1.0
without breaking the existing architecture.

Every contribution should make the project easier to understand,
maintain, and extend.

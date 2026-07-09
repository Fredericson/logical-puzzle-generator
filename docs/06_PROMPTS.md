# PROMPTS.md

# AI Prompt Library
Logical Puzzle Generator

This file contains recommended prompts for AI coding assistants
(Codex, ChatGPT, Claude, Gemini, Cursor, Copilot, etc.).

---

# General Rule

Before every implementation task:

1. Read docs/AI_DEVELOPMENT_SPEC.md
2. Read docs/ARCHITECTURE.md
3. Read docs/CONTRIBUTING_AI.md
4. Read docs/ROADMAP.md
5. Read docs/DECISIONS.md
6. Read the complete repository

Never redesign the architecture.

Return complete files only.

---

# Prompt 1 – Implement Next Commit

```text
Read the complete repository.

Read:
- docs/AI_DEVELOPMENT_SPEC.md
- docs/ARCHITECTURE.md
- docs/CONTRIBUTING_AI.md
- docs/ROADMAP.md
- docs/DECISIONS.md

Implement the next planned commit.

Preserve the architecture.

Return production-ready code.

No placeholders.
No TODOs.
No mock implementations.

Keep public APIs stable.
```

---

# Prompt 2 – Implement Commit 10

```text
Implement Commit 10.

Goal:
Implement the first working puzzle generator.

Create or complete:

- generator/__init__.py
- generator/solution_generator.py
- generator/clue_generator.py
- generator/puzzle_generator.py

Use the existing solver and validator.

Do not redesign any existing subsystem.

Return complete files only.
```

---

# Prompt 3 – Implement Commit 11

```text
Implement Commit 11.

Create PDF generation.

Generate:

- Puzzle PDF
- Solution PDF

Use the existing domain model.

No GUI.
```

---

# Prompt 4 – Implement Commit 12

```text
Implement Commit 12.

Create the Tennis theme.

Include realistic example puzzles.

Keep the architecture unchanged.
```

---

# Prompt 5 – Review the Repository

```text
Review the complete repository.

Focus on:

- correctness
- architecture
- maintainability
- testability
- performance

Do not suggest unnecessary redesign.

Provide concrete improvements only.
```

---

# Prompt 6 – Improve Test Coverage

```text
Review all pytest tests.

Identify missing coverage.

Implement additional tests.

Avoid duplicate tests.
```

---

# Prompt 7 – Fix a Bug

```text
Read the repository.

Find the root cause.

Fix the bug.

Explain briefly why it happened.

Keep the fix minimal.
```

---

# Prompt 8 – Safe Refactoring

```text
Refactor only if it clearly improves readability
or maintainability.

Do not redesign working architecture.

Keep public APIs unchanged.
```

---

# Prompt 9 – Documentation

```text
Update all documentation after implementing
the feature.

Synchronize:

- README
- docs/AI_DEVELOPMENT_SPEC.md
- docs/ARCHITECTURE.md
- docs/CONTRIBUTING_AI.md
- docs/ROADMAP.md
- docs/DECISIONS.md
```

---

# Prompt 10 – Prepare Release 1.0

```text
Prepare Version 1.0.

Tasks:

- verify tests
- verify documentation
- verify generator
- verify PDFs
- remove dead code
- improve comments where necessary

Do not add new features.
```

---

# Prompt 11 – Full Project Review (Recommended)

```text
Read the entire repository before making any changes.

Review:

- architecture
- design
- coding style
- package dependencies
- public APIs
- tests
- documentation

Produce an implementation plan first.

Then implement exactly one logical commit.

Keep the architecture stable.

Return complete files only.

Do not introduce placeholders or TODOs.
```

---

# AI Rules

Always:

- Preserve the architecture.
- Implement one feature per commit.
- Return complete files only.
- Keep code readable.
- Preserve public APIs.
- Follow the existing coding style.
- Prefer small reviewable commits.
- Update tests when needed.
- Update documentation when behaviour changes.

Never:

- Redesign the solver.
- Replace the validator.
- Replace the assignment model.
- Replace the constraint hierarchy.
- Introduce TODOs.
- Introduce placeholder code.
- Invent missing requirements.
- Change package structure without a documented architectural decision.

---

# Primary Objective

The objective is **not** to build the most advanced puzzle generator.

The objective is to finish **Version 1.0**.

Success means:

- Automatic puzzle generation
- Exactly one unique solution
- Puzzle PDF
- Solution PDF
- Tennis example theme
- Clean architecture
- Passing tests

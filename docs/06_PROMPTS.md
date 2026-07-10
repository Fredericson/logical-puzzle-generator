# AI Prompt Library

Reusable prompts for maintaining Logical Puzzle Generator. These prompts assume Version 1.0 is complete and should be adapted to the specific task.

## General maintenance prompt

```text
Read the repository documentation and relevant source files before making changes.

Preserve the Version 1.0 architecture:
- model objects remain behavior-light;
- constraints remain independent matches() implementations;
- solver and validator remain the verification boundary;
- PuzzleGenerator remains the orchestration boundary;
- PDF remains presentation-only, including A4 child-friendly lineup rendering.
- Localization remains presentation-only and must not affect solver, validator, constraints, or generation semantics.

Make the smallest safe change, update tests and documentation when needed, and keep public APIs stable unless explicitly requested otherwise. If PDF presentation changes, verify German and English output and keep puzzle and solution layout sharing free of solving logic.
```

## Bug fix prompt

```text
Investigate the reported bug in the current implementation.

Find the root cause in source and tests.
Implement the smallest fix that preserves public APIs and architecture boundaries.
Add or update tests that would have caught the bug.
Update documentation only if user-facing behavior or commands change.
```

## Documentation synchronization prompt

```text
Synchronize documentation with the current implementation.

Review README.md, docs/, examples/, public APIs, commands, and tests.
Correct stale package descriptions, examples, roadmap claims, and ADR contradictions.
Do not change functional behavior.
```

## Architecture review prompt

```text
Review the repository for architecture drift.

Compare docs/02_ARCHITECTURE.md and docs/05_DECISIONS.md against the implementation.
Identify mismatches, unnecessary coupling, or stale descriptions.
Do not propose a redesign unless there is a concrete correctness or maintainability issue.
```

## Test coverage prompt

```text
Review pytest coverage for the changed area.

Add focused tests for public behavior, edge cases, and regression risks.
Avoid duplicate tests and implementation-detail assertions unless needed to preserve Version 1.0 boundaries.
Run the relevant test subset and full pytest suite when practical.
```

## Release preparation prompt

```text
Prepare a release-quality maintenance change.

Verify installation instructions, command examples, public API examples, language examples, tests, roadmap status, ADRs, and architecture documentation.
Do not add new features.
Limit code changes to release metadata, comments, documentation examples, or obvious inconsistencies.
```


## Difficulty label prompt note

When changing PDF difficulty presentation, keep numeric difficulty metadata semantic and localize child-facing labels only in the presentation/localization layer. Puzzle and solution PDFs should share the same mapping and must not show raw difficulty numbers.

### Difficulty estimation prompts

For difficulty work, keep `DifficultyPolicy` in the generator layer and calculate from final visible constraints after reduction. CLI/API difficulty selection is supported; generation retries until the requested fixed-position-count rule matches. Do not add PDF scoring logic or translation-layer estimation.

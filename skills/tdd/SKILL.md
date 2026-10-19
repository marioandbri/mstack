---
name: tdd
description: Implement features with behavior-first tests and a verified functional smoke, including when the user does not mention TDD. Also use for requested test-first bug fixes and integration tests. Skip explanation-only, read-only review and changes without runtime behavior.
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle — consult them before and during the loop, not after.

When exploring the codebase, read `CONTEXT.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification — "user can checkout with valid cart" tells you exactly what capability exists — and survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams — where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

Reuse test boundaries and acceptance already agreed in the interview, spec or
tickets. Do not ask for that approval again. Inspect existing public interfaces
and tests before proposing a new boundary. Resolve technical choices within the
approved scope; ask when a missing behavioral expectation or new scope decision
needs the user's direction. Tests must exercise the behavior, not an unapproved
interpretation or private implementation details.

## Anti-patterns

- **Implementation-coupled** — mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological** — the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth — a known-good literal, a worked example, the spec.
- **Horizontal slicing** — writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead — one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (see the `code-review` skill), not the red → green implementation cycle.

## Functional smoke and retained evidence

After the red-green cycles, check the main functional path through the real
entrypoint, UI, API, CLI or public library interface as appropriate. Reuse or
extend an existing integrated test when it covers the path. Do not add a duplicate
smoke merely to satisfy a label. Starting the application without checking the
expected effect is insufficient.

Automate the smoke and retain it in the normal suite once stable and repeatable.
Keep necessary assertions and test data independent of the implementation. Use
local-env only when the checks require running services or test databases.

Report the path, expected effect, tested version, relevant environment, execution
command and observed result, linked to existing runner output. Preserve red and
green evidence for new behavior. Mark unexecuted, blocked and failing checks
accurately. Do not optimize for a coverage metric at the expense of behavior.

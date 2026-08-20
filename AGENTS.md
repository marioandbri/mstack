# Engineering skills repository

This repository is canonical source for Mario's managed workflow skills.

## Rules

- Edit skills here, never installed symlink paths as independent copies.
- Keep `skills.json`, `UPSTREAM.md`, and license notices aligned with imports.
- Preserve Agent Skills compatibility: valid frontmatter, matching directory/name, concise descriptions, and relative links.
- Keep skill entry points concise. Move detailed material into same skill directory.
- Use fish for installation scripts and Bun `1.3.14` for validation/tests.
- Installer must default to dry-run, back up conflicts, and remain idempotent.
- Do not add external skill without license and provenance review.
- Do not add a dependency or CLI without exact version pin.
- Apply `unslop` to repository prose.
- Never edit generated changelogs.

## Verification

Before completion:

```fish
bun run check
bun test
fish install/verify.fish
```

When installer changes, also run tests against temporary HOME and confirm dry-run makes no changes.

## Knowledge Gathered

### Ownership

- Repository owns 24 workflow skills listed in `skills.json`.
- Specialized frontend, browser, and package-provided skills remain external.
- Imported skills update through deliberate review, never automatic replacement.

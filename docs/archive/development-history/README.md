# Development History Archive

This directory is the future home for historical development notes that are no longer part of the active product documentation.

`docs/codex remains temporarily for legacy tests/checkers`. Many older smoke tests and checker scripts still read stage documents directly from `docs/codex/*.md`. A physical move of those files is therefore blocked until **KR-2** rewrites stage-specific tests and checker scripts into product workflow tests.

Canonical product docs now live under:

- `docs/product/`
- `docs/workflows/`
- `docs/quality/`
- `docs/operators/`
- `docs/architecture/`

Archive policy:

1. Keep `docs/codex` in place while legacy checkers depend on it.
2. Treat `docs/codex` as deprecated development history, not product documentation.
3. Move files here only after the corresponding legacy checker/test dependency is removed or rewritten.
4. Do not encode local machine paths, profile names, branch names, or commit hashes in archive policy.

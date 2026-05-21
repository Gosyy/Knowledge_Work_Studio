# KR-1B-R2 Stage Documentation Deprecation

KR-1B-R2 replaces the failed physical archive attempt with a safe deprecation index.

## Purpose

Make the documentation hierarchy honest without breaking legacy tests:

- product docs are canonical;
- stage docs are deprecated development history;
- physical archive is postponed until KR-2 rewrites legacy checkers.

## Non-goals

- No deletion of `docs/codex` files.
- No movement of `docs/codex` files.
- No weakening of product docs checks.
- No claim that stage-test cleanup is complete.

## Acceptance

- Product documentation skeleton remains ready.
- Stage deprecation checker is ready.
- Full runner remains green.
- Docker smoke remains green.

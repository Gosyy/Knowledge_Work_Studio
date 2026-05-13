# S13g — canonical schema adapter + minimal strict rerun

S13g changes the live benchmark strategy after S13d/S13f showed that asking GigaChat to emit a large strict schema is unreliable.

## Goal

Use a small model-facing JSON contract and a deterministic KW Studio canonical adapter.

The adapter must keep provenance clear:

- model-provided content remains identified as model-provided;
- adapter-added workflow metadata is explicitly marked as adapter-added;
- adapter fields are not treated as raw model output;
- human review remains required.

## Scope

S13g adds:

- minimal prompt contract;
- canonical schema adapter;
- adapter provenance contract;
- live minimal rerun script;
- checker and smoke tests.

## Boundaries

S13g does not:

- call GigaChat in static/targeted/full runner checks;
- store credential values;
- complete human review;
- auto-approve scenarios;
- claim selected offline workflow parity;
- claim Kimi-level achieved;
- verify Server 3 local_intranet route.

## Acceptance

Static acceptance requires:

- 12 scenario policies;
- minimal prompt required;
- canonical adapter required;
- adapter provenance required;
- deterministic normalization required;
- clear model-vs-adapter field separation;
- no parity/Kimi/Server 3 claims.

Execution acceptance is separate and requires a live S13g run with 12/12 canonical-valid scenarios.

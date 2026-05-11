# S13b — Live public_api_dev GigaChat generation for selected benchmark scenarios

S13b installs the strict live-generation workflow for the twelve selected S10 benchmark scenarios.

## Scope

S13b is the controlled bridge from S13a packet skeletons to real model-assisted benchmark evidence. It requires the `public_api_dev` GigaChat route and shell-provided credentials when the explicit live command is run.

## Required boundary

- Credentials must come from shell environment variables only.
- Raw credential values must never be committed, logged, or stored in generated manifests.
- `public_api_dev` is real provider evidence through the internet/key route.
- `public_api_dev` is not proof of the production Server 3 `local_intranet` route.
- S13b generation alone does not complete human review.
- S13b generation alone does not support selected offline workflow parity.
- Generic `Kimi-level achieved` and whole-project Kimi parity claims remain forbidden.

## Static readiness versus live execution

The production readiness gate uses the static S13b checker. This confirms that the live execution workflow is configured and safe, but it does not call GigaChat and does not require credentials.

The explicit live command must be run separately with shell env credentials. Its artifacts are handoff/evidence artifacts and must not be committed.

## Live outputs

For each selected benchmark scenario, S13b live execution must produce:

- scenario generation manifest JSON;
- scenario model response JSON;
- approved plan candidate JSON;
- artifact generation request JSON;
- safe metadata JSON;
- citation manifest placeholder JSON;
- render QA input placeholder JSON.

## Follow-up

S13c should package the generated S13b live artifacts into a human review packet. Completed human review results must still be collected and ingested before the accepted future claim can be considered:

`Kimi Slides-class offline workflow parity for selected benchmark scenarios.`

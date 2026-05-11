# S13d — Live benchmark prompt/schema hardening and rerun

S13d hardens the S13b live `public_api_dev` GigaChat benchmark path after the first real 12-scenario run produced usable but overly generic planning evidence.

## Scope

S13d adds a strict prompt/schema contract and an explicit hardened live rerun script. The normal targeted tests, full runner, and Docker smoke do not call the live GigaChat endpoint and do not require credentials.

## Hardened output requirements

Each scenario response must be a single JSON object with:

- scenario-specific summary;
- approved plan candidate;
- at least eight slide outline entries;
- native PPTX visual plan;
- slide-level citation obligations;
- render QA obligations;
- evidence manifest plan;
- human review handoff;
- claim-safety boundaries.

## Safety boundaries

S13d does not claim selected parity, does not complete human review, does not auto-approve scenarios, does not record credential values, and does not verify Server 3 `local_intranet`.

The live rerun remains `public_api_dev` provider evidence only. It is not production/offline Server 3 proof.

## Next step

After S13d patch-stage closure, run the explicit hardened live rerun with shell env credentials, export a new evidence packet, and collect real completed human review results before any selected offline workflow parity claim.

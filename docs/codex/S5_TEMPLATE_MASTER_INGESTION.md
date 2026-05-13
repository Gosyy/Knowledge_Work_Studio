# S5 — Template and slide-master ingestion

- status: `controlled_template_master_ingestion_contract`
- branch: `9_Product_Release_Hardening`
- baseline before S5: `f04190dc56d7817401482f04b1289aa6bb2d0a6e`
- Kimi-level claimed: `False`

## Purpose

S5 makes local PPTX template and slide-master ingestion explicit and testable for the S-phase Kimi Slides-class workflow track. It connects the existing local template registry to the S3 adaptive deck modes and S4 native visual specifications.

The goal is not cloud template discovery. The goal is offline/intranet-safe template handling: extract local master/theme/layout metadata, map deck archetypes to available layouts, and guarantee that native PPTX tables, charts, and diagrams have a compatible local layout target.

## Required controls

S5 requires:

- a local template registry as the only template source;
- extracted template metadata: theme name, font family, colors, and layout IDs;
- explicit rejection of URL, filesystem-path, and external template references;
- S3 deck-mode archetype to local slide-layout mapping;
- S4 native visual to local slide-layout mapping;
- editable PPTX and provenance expectations preserved across template mode;
- no public-internet dependency.

## Acceptance

S5 is accepted when the checker reports:

- `template_master_ingestion_completed_by_s5 = true`;
- every local template exposes master/theme/layout metadata;
- all five S3 deck modes have template layout mappings;
- S4 native visuals are mapped to local template layouts;
- external template discovery is disabled;
- Kimi-level and Server 3 local-intranet verification are not claimed.

## Boundaries

S5 does not add API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker changes, cloud LLM, cloud vision, public-internet production dependency, Kimi-level claim, or Server 3 local-intranet verification claim.

## Next step

The next controlled phase is `S6 — image/screenshot-to-slide workflow through local heavy modules`.

# S7 - Offline/intranet research citations

- status: `controlled_offline_intranet_research_citations`
- branch: `9_Product_Release_Hardening`
- baseline before S7: `7a0e6732429b6fc9e29e78ef49453f6715f320d3`
- Kimi-level claimed: `False`

## Purpose

S7 adds the source-grounded citation contract needed for Kimi Slides-class offline/intranet workflows. The goal is to make every slide-level claim, native table/chart/diagram element, and S6 image-region reconstruction traceable to an allowed local or intranet source.

S7 is not a public-web research feature. It is an offline/intranet citation manifest and coverage layer.

## Allowed source types

S7 allows only source types that can be represented inside the deployment boundary:

- uploaded documents;
- internal browser evidence packets that were captured and stored locally;
- local knowledge-base entries;
- intranet documents;
- S6 image-region evidence;
- generated artifact manifests and safe metadata.

Hidden public-web lookups, cloud search results, cloud vision results, and unattributed model memory are explicitly forbidden as production-default citation sources.

## Citation manifest contract

Every citation entry must carry stable safe fields:

- citation id;
- source type;
- source id;
- fragment id;
- claim id;
- slide id;
- evidence summary;
- locator;
- provenance digest.

The required manifest sections are sources, fragments, slide claims, citations, coverage summary, and offline boundary.

## S4/S6 integration

S7 connects directly to prior S-phase work:

- S4 native PPTX tables, charts, and diagrams must cite source fragments for cells, series, nodes, and decisions.
- S6 image/screenshot regions must cite the source image crop region and reconstructed slide element.
- Raster fallback is not accepted as a primary citation path.

## Acceptance

S7 is accepted when:

- `kw_s7_offline_research_citations_check.py --require-ready` reports ready;
- targeted S7 smoke tests pass;
- production readiness `--checks-only` passes;
- full runner passes after commit and push;
- Docker smoke passes after commit and push.

## Non-goals

S7 does not add public API endpoints, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or hidden public-internet production dependency.

S7 does not claim Kimi-level parity and does not verify Server 3 `local_intranet` route.

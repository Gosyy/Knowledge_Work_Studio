# S9 - Render-based visual QA

- status: `controlled_render_based_visual_qa_contract`
- branch: `9_Product_Release_Hardening`
- baseline before S9: `79e4e71463f2a68668c039f2e9f35d6faabe7f52`
- Kimi-level claimed: `False`

## Purpose

S9 turns the S-phase visual-quality target into an offline/intranet-safe render-based QA contract. It requires actual rendered slide evidence and geometry manifests rather than relying only on semantic or metadata checks.

The checkpoint is designed to catch the failure class discovered in the P10 review chain: automated QA can look good while a human sees overlap, clipped text, tiny unreadable elements, dense tables, or visual collisions.

## Render evidence inputs

S9 requires these local evidence inputs for future runtime implementations:

1. rendered slide screenshot or equivalent local render image;
2. slide geometry manifest;
3. native visual geometry manifest from S4 tables/charts/diagrams;
4. S6 image-region reconstruction manifest when image/screenshot evidence is used;
5. S7 citation manifest for claim and visual evidence linkage;
6. S8 revised plan snapshot metadata for conversational edits.

## Required visual checks

The S9 contract requires checks for:

- title/body collision;
- text box overlap;
- clipped text;
- tiny text;
- table overflow;
- dense native visual regions;
- chart label collision;
- diagram node overlap;
- image reconstruction mismatch;
- citation/provenance marker visibility.

## Offline/intranet boundary

S9 does not introduce cloud vision, public internet, browser automation, dependency changes, Docker changes, frontend runtime changes, API endpoints, or database migrations.

Future implementations may use local render tools and local image analysis modules on Server 2. They must not silently fall back to cloud vision.

## Acceptance

S9 is accepted when the checker confirms render evidence requirements, all visual defect checks, compatibility with S3/S4/S6/S7/S8, offline/intranet boundaries, no Kimi-level claim, and production readiness gate integration.

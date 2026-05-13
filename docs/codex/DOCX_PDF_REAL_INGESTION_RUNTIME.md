# RF3 DOCX/PDF Real Ingestion Runtime

## Status

RF3 adds a narrow offline runtime path for real DOCX and PDF ingestion after RF2 slides runtime foundation closure.

This is Runtime Foundation work. It does not start K-phase, does not add cloud OCR, and does not claim whole-project Kimi-level capability.

## Runtime paths

### DOCX

RF3 supports local extraction from real DOCX packages:

```text
DOCX bytes
→ validate ZIP package
→ read word/document.xml
→ extract WordprocessingML text paragraphs
→ emit text/plain ingestion report + safe metadata
```

The DOCX path uses only Python standard library ZIP/XML parsing. It rejects malformed/non-DOCX bytes instead of fabricating success.

### PDF

RF3 supports local extraction from a PDF text layer:

```text
PDF bytes
→ validate PDF marker
→ parse local text-show operators
→ normalize extracted text
→ emit summary text report + safe metadata
```

RF3 does not add OCR and must not fake scanned PDF support.

Image-only/scanned PDFs fail honestly with an explicit OCR-not-implemented error. This preserves operator trust until a later OCR/heavy-node runtime is introduced.

## Safety guarantees

RF3 guarantees:

- no public API endpoint;
- no DB schema migration;
- no queue/event-store migration;
- no dependency version changes;
- no Dockerfile changes;
- no cloud OCR;
- no fake OCR claims;
- no browser runtime;
- no LLM topology changes;
- no K-phase start;
- no Kimi-level claim.

## Safe metadata

DOCX/PDF ingestion outputs include safe runtime metadata:

- `workflow_id`;
- `schema_version`;
- `source_format`;
- `source_filename`;
- extracted text counters;
- content type;
- `network_required: false`;
- `cloud_ocr_used: false`;
- `fake_ocr_claimed: false`;
- `dependency_versions_changed_by_rf3: false`;
- `dockerfiles_changed_by_rf3: false`;
- `whole_project_kimi_level_supported: false`.

## Acceptance

RF3 is accepted when:

- `python3 scripts/kw_docx_pdf_real_ingestion_check.py --repo-root . --require-ready --json` passes;
- RF3 smoke tests prove real DOCX package extraction;
- RF3 smoke tests prove PDF text-layer extraction;
- image-only/scanned PDFs fail honestly without OCR claims;
- existing DOCX/PDF service tests still pass;
- production readiness includes the RF3 checker;
- full runner and Docker runtime smoke pass after commit and push.

## Next step

After RF3 acceptance, continue to:

```text
RF4 — Local GigaChat integration hardening
```

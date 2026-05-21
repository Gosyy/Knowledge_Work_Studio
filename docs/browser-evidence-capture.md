# Browser Evidence Capture Contract

S8 defines the contract for browser-assisted internal evidence capture.

Scope:
- internal/intranet pages only;
- explicit operator approval before capture;
- safe metadata and artifact references only;
- evidence is represented by artifact ids and integrity metadata;
- captured browser evidence links into the S7 slides provenance manifest.

This is a contract-only step. It does not introduce an autonomous browser agent and it does not require public internet access.

The redaction policy forbids raw credentials, cookies, storage dumps, raw DOM/HTML, screenshots as pixels, and unredacted token-like values in captured payloads. The policy catalog is allowed to name blocked key categories, but runtime payload validation excludes the policy catalog itself from evidence scanning.

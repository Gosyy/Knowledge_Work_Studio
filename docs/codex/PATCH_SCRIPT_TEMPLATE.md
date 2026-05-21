# Python Apply Script Template

Use this template for repo-root patch scripts.

```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_PATHS = [
    "AGENTS.md",
    "backend",
    "frontend",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def pass_(message: str) -> None:
    print(f"[PASS] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def repo_root() -> Path:
    root = Path.cwd()
    missing = [path for path in REQUIRED_PATHS if not (root / path).exists()]
    if missing:
        fail("run from repository root; missing: " + ", ".join(missing))
    return root


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        ok(f"{label} already applied")
        return
    if old not in text:
        fail(f"missing anchor for {label}: {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    pass_(label)


def write_new(path: Path, content: str, label: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            ok(f"{label} already exists")
            return
        fail(f"refusing to overwrite existing different file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    pass_(label)


def main() -> int:
    root = repo_root()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Requirements:
- deterministic;
- repo-root only;
- no network;
- no secret printing;
- explicit anchors;
- no broad rewrites unless explicitly allowed;
- no temporary tracked files.

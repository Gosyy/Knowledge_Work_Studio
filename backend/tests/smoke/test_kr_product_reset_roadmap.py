from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ROADMAP = REPO_ROOT / "docs" / "refactor" / "KR_PRODUCT_RESET_ROADMAP.md"


def test_kr_product_reset_roadmap_exists() -> None:
    assert ROADMAP.exists(), "KR product reset roadmap must be documented for future patches"


def test_kr_product_reset_roadmap_covers_product_pillars() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for phrase in [
        "artifact-first",
        "provenance-first",
        "operator-gated",
        "offline/intranet",
        "DOCX workflow",
        "PDF workflow",
        "XLSX / Excel workflow",
        "Slides workflow",
        "Python analysis workflow",
        "Browser-assisted evidence workflow",
    ]:
        assert phrase in text


def test_kr_product_reset_roadmap_covers_next_phases_and_closure_rules() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for phrase in [
        "KR-3E",
        "KR-3F",
        "KR-4A",
        "KR-5A",
        "KR-5B",
        "KR-6A",
        "full runner",
        "Docker smoke",
        "GigaChat",
        "WorkflowInput",
        "WorkflowProvenance",
    ]:
        assert phrase in text

from __future__ import annotations

from pathlib import Path

from scripts.kw_system_dependencies_check import REQUIRED_UBUNTU_PACKAGES, validate_package_file


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_FILE = REPO_ROOT / "infra" / "system-packages" / "ubuntu-render-stack.txt"
SYSTEM_DEPENDENCIES_DOC = REPO_ROOT / "docs" / "operators" / "SYSTEM_DEPENDENCIES.md"


def test_system_dependency_package_file_tracks_required_office_render_stack() -> None:
    report = validate_package_file(REPO_ROOT)
    assert report["status"] == "ready"
    assert "libreoffice-impress" in REQUIRED_UBUNTU_PACKAGES
    assert "poppler-utils" in REQUIRED_UBUNTU_PACKAGES
    assert "fonts-liberation" in REQUIRED_UBUNTU_PACKAGES


def test_system_dependency_operator_doc_names_installer_and_validation() -> None:
    text = SYSTEM_DEPENDENCIES_DOC.read_text(encoding="utf-8")
    assert "scripts/dev/install_system_dependencies_ubuntu.sh" in text
    assert "scripts/kw_system_dependencies_check.py" in text
    assert "infra/system-packages/ubuntu-render-stack.txt" in text
    assert "LibreOffice Impress" in text or "libreoffice-impress" in text


def test_backend_dockerfile_installs_declared_system_dependency_list() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile.backend").read_text(encoding="utf-8")
    assert "infra/system-packages/ubuntu-render-stack.txt" in dockerfile
    assert "apt-get install" in dockerfile
    assert "grep -vE" in dockerfile
    assert "xargs -r apt-get install" in dockerfile
    assert "xargs -a ./infra/system-packages/ubuntu-render-stack.txt" not in dockerfile


def test_backend_dockerfile_ignores_package_list_comments() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile.backend").read_text(encoding="utf-8")
    assert "^[[:space:]]*(#|$)" in dockerfile

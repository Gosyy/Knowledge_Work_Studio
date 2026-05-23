from pathlib import Path


def test_pytest_collection_is_scoped_away_from_runtime_logs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    pytest_ini = repo_root / "pytest.ini"
    assert pytest_ini.exists()
    content = pytest_ini.read_text(encoding="utf-8")
    assert "testpaths = backend/tests" in content
    assert "logs" in content
    assert "storage" in content


def test_production_readiness_backend_pytest_targets_backend_tests() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    gate_source = (repo_root / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert '(python, "-m", "pytest", "backend/tests", "-q")' in gate_source
    assert '(python, "-m", "pytest", "-q")' not in gate_source

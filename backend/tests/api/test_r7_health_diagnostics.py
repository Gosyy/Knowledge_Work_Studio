import json

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_r7_health_contract_is_preserved() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_r7_ready_exposes_safe_operator_fields_without_secret_values() -> None:
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert "status" in payload
    assert "deployment_mode" in payload
    assert "metadata_backend" in payload
    assert "storage_backend" in payload
    assert "llm_provider" in payload
    assert "checks" in payload
    assert "errors" in payload
    assert "warnings" in payload

    serialized = json.dumps(payload)
    assert "super-secret-r7-value" not in serialized
    assert "postgresql://" not in serialized.lower()
    assert "client_secret" not in serialized.lower()

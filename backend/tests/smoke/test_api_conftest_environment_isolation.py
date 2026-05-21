from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path


def test_api_conftest_import_restores_operator_environment() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    code = textwrap.dedent(
        """
        from __future__ import annotations

        import importlib.util
        import json
        import os
        import sys
        from pathlib import Path

        keys = [
            "APP_ENV",
            "DEPLOYMENT_MODE",
            "METADATA_BACKEND",
            "SQLITE_RUNTIME_ALLOWED",
            "STORAGE_BACKEND",
            "LLM_PROVIDER",
            "FAKE_LLM_RESPONSE",
        ]
        os.environ["APP_ENV"] = "production"
        os.environ["DEPLOYMENT_MODE"] = "offline_intranet"
        os.environ["METADATA_BACKEND"] = "postgres"
        os.environ["SQLITE_RUNTIME_ALLOWED"] = "false"
        os.environ["STORAGE_BACKEND"] = "local"
        os.environ["LLM_PROVIDER"] = "gigachat"
        os.environ.pop("FAKE_LLM_RESPONSE", None)

        path = Path("backend/tests/api/conftest.py")
        spec = importlib.util.spec_from_file_location("kw_api_conftest_env_probe", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load API conftest module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        print(json.dumps({key: os.environ.get(key) for key in keys}, sort_keys=True))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload == {
        "APP_ENV": "production",
        "DEPLOYMENT_MODE": "offline_intranet",
        "METADATA_BACKEND": "postgres",
        "SQLITE_RUNTIME_ALLOWED": "false",
        "STORAGE_BACKEND": "local",
        "LLM_PROVIDER": "gigachat",
        "FAKE_LLM_RESPONSE": None,
    }

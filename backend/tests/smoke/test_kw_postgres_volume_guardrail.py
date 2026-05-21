from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path("scripts/deploy/kw_postgres_volume_guardrail.py")


def load_guardrail_module():
    spec = importlib.util.spec_from_file_location("kw_postgres_volume_guardrail", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses on Python 3.14 expect manually loaded modules to be present
    # in sys.modules before exec_module when postponed annotations are used.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_postgres_volume_guardrail_uses_compose_labels_not_profile_paths() -> None:
    module = load_guardrail_module()
    command = module.build_volume_ls_command("kw-studio", "postgres_data")

    assert command[:4] == ["docker", "volume", "ls", "-q"]
    assert "label=com.docker.compose.project=kw-studio" in command
    assert "label=com.docker.compose.volume=postgres_data" in command

    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "/home/su4ka" not in source
    assert "/home/editor" not in source
    assert "D:\\" not in source


def test_postgres_volume_guardrail_requires_explicit_confirmation() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "--confirm-reset-postgres-volume" in source
    assert "refusing to remove metadata volume" in source
    assert "Storage/artifact volumes are intentionally not removed" in source


def test_postgres_volume_guardrail_remove_command_targets_single_named_volume() -> None:
    module = load_guardrail_module()

    assert module.POSTGRES_VOLUME_LABEL_VALUE == "postgres_data"
    assert module.build_volume_rm_command("kw-studio_postgres_data") == [
        "docker",
        "volume",
        "rm",
        "kw-studio_postgres_data",
    ]

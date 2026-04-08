import asyncio

from backend.app.runtime.browser import BrowserSupervisor, load_browser_runtime_config
from backend.app.runtime.browser.utils import BrowserRuntimeConfig


class FlakyController:
    name = "flaky"

    def __init__(self) -> None:
        self.running = False
        self.health_checks = 0

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def is_healthy(self) -> bool:
        self.health_checks += 1
        if self.health_checks == 1:
            return False
        return self.running


class StableController:
    name = "stable"

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def is_healthy(self) -> bool:
        return self.running


def test_browser_runtime_config_is_env_gated(monkeypatch) -> None:
    monkeypatch.delenv("KW_BROWSER_RUNTIME_ENABLED", raising=False)
    monkeypatch.delenv("KW_BROWSER_ALLOW_UNSAFE", raising=False)
    monkeypatch.delenv("KW_BROWSER_BACKEND", raising=False)

    config = load_browser_runtime_config()
    assert config.enabled is False
    assert config.allow_unsafe_features is False
    assert config.preferred_backend == "playwright"


def test_browser_supervisor_start_stop_and_restart_smoke() -> None:
    config = BrowserRuntimeConfig(
        enabled=True,
        preferred_backend="playwright",
        allow_unsafe_features=False,
        max_restart_attempts=2,
    )
    controller = FlakyController()
    supervisor = BrowserSupervisor(config=config, controller=controller)

    asyncio.run(supervisor.start())
    assert asyncio.run(supervisor.ensure_healthy()) is True
    assert supervisor.restart_count == 1

    asyncio.run(supervisor.stop())
    assert controller.running is False


def test_browser_supervisor_respects_disabled_runtime() -> None:
    config = BrowserRuntimeConfig(
        enabled=False,
        preferred_backend="cdp",
        allow_unsafe_features=False,
        max_restart_attempts=1,
    )
    controller = StableController()
    supervisor = BrowserSupervisor(config=config, controller=controller)

    asyncio.run(supervisor.start())

    assert controller.running is False

def test_browser_supervisor_from_env_selects_backend(monkeypatch) -> None:
    monkeypatch.setenv("KW_BROWSER_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("KW_BROWSER_BACKEND", "cdp")

    supervisor = BrowserSupervisor.from_env()
    assert supervisor.controller.name == "cdp"

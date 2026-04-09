from __future__ import annotations

from dataclasses import dataclass
import logging

from backend.app.runtime.browser.cdp_controller import CDPController
from backend.app.runtime.browser.playwright_controller import PlaywrightController
from backend.app.runtime.browser.utils import BrowserController, BrowserRuntimeConfig, load_browser_runtime_config

logger = logging.getLogger(__name__)


@dataclass
class BrowserSupervisor:
    config: BrowserRuntimeConfig
    controller: BrowserController
    restart_count: int = 0

    @classmethod
    def from_env(cls) -> "BrowserSupervisor":
        config = load_browser_runtime_config()
        controller: BrowserController
        if config.preferred_backend == "cdp":
            controller = CDPController(config=config)
        else:
            controller = PlaywrightController(config=config)
        return cls(config=config, controller=controller)

    async def start(self) -> None:
        if not self.config.enabled:
            logger.info("Browser supervisor start skipped because runtime is disabled")
            return
        await self.controller.start()

    async def stop(self) -> None:
        await self.controller.stop()

    async def ensure_healthy(self) -> bool:
        if not self.config.enabled:
            return False

        healthy = await self.controller.is_healthy()
        if healthy:
            return True
        if self.restart_count >= self.config.max_restart_attempts:
            return False

        self.restart_count += 1
        logger.warning(
            "Browser controller unhealthy, attempting restart",
            extra={"restart_count": self.restart_count, "controller": self.controller.name},
        )
        await self.controller.stop()
        await self.controller.start()
        return await self.controller.is_healthy()

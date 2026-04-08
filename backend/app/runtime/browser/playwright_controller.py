from __future__ import annotations

from dataclasses import dataclass
import logging

from backend.app.runtime.browser.utils import BrowserRuntimeConfig

logger = logging.getLogger(__name__)


@dataclass
class PlaywrightController:
    config: BrowserRuntimeConfig
    name: str = "playwright"

    _running: bool = False

    async def start(self) -> None:
        if not self.config.enabled:
            raise RuntimeError("Browser runtime is disabled")
        self._running = True
        logger.info("Playwright controller started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Playwright controller stopped")

    async def is_healthy(self) -> bool:
        return self._running

    def unsafe_mode_enabled(self) -> bool:
        return self.config.allow_unsafe_features

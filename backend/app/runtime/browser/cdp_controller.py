from __future__ import annotations

from dataclasses import dataclass
import logging

from backend.app.runtime.browser.utils import BrowserRuntimeConfig

logger = logging.getLogger(__name__)


@dataclass
class CDPController:
    config: BrowserRuntimeConfig
    name: str = "cdp"

    _running: bool = False

    async def start(self) -> None:
        if not self.config.enabled:
            raise RuntimeError("Browser runtime is disabled")
        self._running = True
        logger.info("CDP controller started")

    async def stop(self) -> None:
        self._running = False
        logger.info("CDP controller stopped")

    async def is_healthy(self) -> bool:
        return self._running

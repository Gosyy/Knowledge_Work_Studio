from __future__ import annotations

import logging

from backend.app.core.config import get_settings
from backend.app.integrations.database import initialize_database

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    initialize_database(get_settings())
    logger.info("Baseline migration applied (or already present).")

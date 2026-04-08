from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from backend.app.api.routes import get_api_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting KW Studio backend")
    yield
    logger.info("Stopping KW Studio backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="KW Studio API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(get_api_router())
    return app


app = create_app()

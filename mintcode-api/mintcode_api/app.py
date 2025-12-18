from __future__ import annotations

from fastapi import FastAPI

from mintcode_api.db import Base, engine
from mintcode_api.routes_admin import router as admin_router
from mintcode_api.routes_health import router as health_router
from mintcode_api.routes_redeem import router as redeem_router


def create_app() -> FastAPI:
    app = FastAPI(title="mintcode-api")

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(redeem_router)
    return app


app = create_app()

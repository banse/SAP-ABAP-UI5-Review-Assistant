"""SAP ABAP/UI5 Review Assistant — FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db.connection import close_db, init_db

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ANN201, ARG001
    """Startup/shutdown lifecycle: initialise and tear down the DB pool."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="SAP ABAP/UI5 Review Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> FileResponse:
    """Serve the single-page frontend."""
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, object]:
    from app.db.connection import get_session_factory

    db_available = get_session_factory() is not None
    return {"status": "ok", "db_available": db_available}


# Mount static files AFTER explicit routes so that named routes take priority.
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

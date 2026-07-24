import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import Base, engine
from app.routers import complaints

logger = logging.getLogger("uvicorn.error")

try:
    from app.routers import ai as ai_router
    HAS_AI_ROUTER = True
except ImportError:
    HAS_AI_ROUTER = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Customer Complaint Management API",
    description="API & FDF Quality Assurance Module — Customer Complaint intake, triage and AI-assisted extraction.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    origin = request.headers.get("origin")
    headers = {}
    if origin and origin == settings.frontend_origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc.__class__.__name__}: {exc}"},
        headers=headers,
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok", "env": settings.app_env}


app.include_router(complaints.router)

if HAS_AI_ROUTER:
    app.include_router(ai_router.router)
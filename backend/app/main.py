"""
AutoTestAI - Main FastAPI Application
Entry point for the backend server.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, ensure_directories
from app.api.upload import router as upload_router
from app.api.generate import router as generate_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"🤖 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"   AI Provider: {settings.ACTIVE_AI_PROVIDER.value}")
    logger.info(f"   Debug Mode: {settings.DEBUG}")
    logger.info("=" * 60)
    ensure_directories()
    yield
    # Shutdown
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered agent that converts manual test cases into "
        "production-ready test automation code with frameworks and reports."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload_router)
app.include_router(generate_router)


# ── Health & Info Endpoints ───────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — API health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "ai_provider": settings.ACTIVE_AI_PROVIDER.value,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "ai_provider": settings.ACTIVE_AI_PROVIDER.value,
        "upload_dir": settings.UPLOAD_DIR,
        "output_dir": settings.OUTPUT_DIR,
    }


@app.get("/api/config/ai-providers", tags=["Configuration"])
async def get_ai_providers():
    """Get available AI providers and their status."""
    providers = {
        "openai": {
            "available": bool(settings.OPENAI_API_KEY),
            "model": settings.OPENAI_MODEL,
            "active": settings.ACTIVE_AI_PROVIDER.value == "openai",
        },
        "gemini": {
            "available": bool(settings.GEMINI_API_KEY),
            "model": settings.GEMINI_MODEL,
            "active": settings.ACTIVE_AI_PROVIDER.value == "gemini",
        },
        "ollama": {
            "available": True,  # Always available if Ollama is running
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
            "active": settings.ACTIVE_AI_PROVIDER.value == "ollama",
        },
    }
    return {"providers": providers, "active": settings.ACTIVE_AI_PROVIDER.value}

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware

from app.routers.users import router as users_router
from app.routers.boards import router as boards_router
from app.routers.threads import router as threads_router
from app.routers.posts import router as posts_router
from app.routers.websocket import router as websocket_router
from app.routers.ritual_admin import router as ritual_admin_router
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.core.settings import settings
from app.middleware.ritual_middleware import RitualMiddleware
# Import all models to register them with Base.metadata
from app.models import User, Board, Thread, Post, Media  # noqa: F401

# Configure logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Starting Cursed Board API...")

    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Initialize Redis
    try:
        redis_client = await init_redis()
        logger.info("Redis connected")
        app.state.redis = redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Cursed Board API...")
    await engine.dispose()
    await close_redis()
    logger.info("Cleanup complete")


app = FastAPI(
    title="Cursed Board",
    version="1.0.0",
    description="Cursed Forum API - where the posts know you're reading them",
    lifespan=lifespan,
)

# Middleware (order matters: last added = first executed)
# 1. Ritual Middleware - tracks user state
app.add_middleware(RitualMiddleware, ttl=settings.RITUAL_STATE_TTL)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Router
api_router = APIRouter(prefix="/api")
api_router.include_router(users_router)
api_router.include_router(boards_router)
api_router.include_router(threads_router)
api_router.include_router(posts_router)

app.include_router(api_router)
app.include_router(websocket_router)
app.include_router(ritual_admin_router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Cursed Board API is running"}


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    redis_ok = False
    try:
        if hasattr(app.state, "redis"):
            await app.state.redis.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
    }

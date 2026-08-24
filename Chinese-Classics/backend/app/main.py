from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.api.endpoints import auth, chat, history, misc
from app.db import init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing database...")
    await init_db()
    
    # 初始化教程数据
    from app.db import AsyncSessionLocal
    from app.api.endpoints.misc import init_tutorials
    async with AsyncSessionLocal() as db:
        await init_tutorials(db)
    
    logger.info("Database initialized successfully")
    yield
    # 关闭时清理资源
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="国学命理智能体应用API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}", tags=["history"])
app.include_router(misc.router, prefix=f"{settings.API_V1_STR}", tags=["misc"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("health_check_called")
    return {"status": "healthy", "service": "chinese-classics-agent"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Chinese Classics Agent API"}

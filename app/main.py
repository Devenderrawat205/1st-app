import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.initial_data import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API router
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    return application


app = create_application()

# WebSocket connections
active_connections: List[WebSocket] = []

# Store backtest status
backtest_status: Dict[str, Dict[str, Any]] = {}

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize first superuser
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Welcome to Indian Market Backtest API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    # Initialize any resources here


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    # Clean up resources here


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    # Handle subscription to backtest updates
                    backtest_id = message.get("backtest_id")
                    if backtest_id in backtest_status:
                        await websocket.send_json({
                            "type": "status_update",
                            "backtest_id": backtest_id,
                            "status": backtest_status[backtest_id]
                        })
                else:
                    # Echo back other messages
                    await websocket.send_text(f"Message received: {data}")
            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_text(f"Error: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
            await websocket.close()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
from dotenv import load_dotenv
import os
try:
    from alphaVantage.routes import stock_routes
except ModuleNotFoundError:
    from src.alphaVantage.routes import stock_routes
from contextlib import asynccontextmanager
from src.feature.logging import build_app_logger, StdoutLoggingService

load_dotenv()

# Initialize application logger
logger = build_app_logger(handlers=[StdoutLoggingService()])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    environment = os.getenv("ENV", "development")
    logger.info("Application starting", environment=environment)
    yield
    # Shutdown
    logger.info("Application shutting down")
    logger.close()

app = FastAPI(lifespan=lifespan)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001"  # Add this if frontend is on 3001
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include stock-related routes
app.include_router(stock_routes.router)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Stock API"}

@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy"}

if __name__ == "__main__":
    environment = os.getenv("ENV", "development")
    reload_flag = environment == "development"
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=reload_flag)
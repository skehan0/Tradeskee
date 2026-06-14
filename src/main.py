"""
Tradeskee API - Main application entry point.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import stock_routes  # Only stock routes for now
from src.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional stock market analysis API",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "message": "Welcome to Tradeskee API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"http://127.0.0.1:{settings.PORT}{settings.API_V1_PREFIX}/docs",
        "health": f"http://127.0.0.1:{settings.PORT}/health",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Health status and application info
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )


# Include stock routes (only working endpoint for now)
app.include_router(
    stock_routes.router, prefix=f"{settings.API_V1_PREFIX}/stocks", tags=["Stocks"]
)

# TODO: Fix and uncomment these after refactoring
# app.include_router(
#     crypto_routes.router,
#     prefix=f"{settings.API_V1_PREFIX}/crypto",
#     tags=["Crypto"]
# )
# app.include_router(
#     econmic_routes.router,
#     prefix=f"{settings.API_V1_PREFIX}/economic",
#     tags=["Economic"]
# )

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        workers=settings.WORKERS if settings.is_production else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )

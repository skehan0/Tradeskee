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
from logging import info

load_dotenv()

app = FastAPI()

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
    return {"message": "Welcome to the Stock API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    environment = os.getenv("ENV", "development")
    reload_flag = environment == "development"
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=reload_flag)
from fastapi import APIRouter
from src.api.services.crypto_services import fetch_crypto_data

router = APIRouter()

@router.get("/data/{symbol}")
async def get_crypto_data(symbol: str):
    return await fetch_crypto_data(symbol)
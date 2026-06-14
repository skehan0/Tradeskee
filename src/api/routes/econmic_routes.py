from fastapi import APIRouter

from src.api.services.economic_services import fetch_economic_data

router = APIRouter()


@router.get("/data/{indicator}")
async def get_economic_data(indicator: str):
    return await fetch_economic_data(indicator)

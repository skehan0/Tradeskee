from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.database.mongoDB import database as database_module
from src.infrastructure.database.mongoDB.database import DatabaseManager
from src.main import lifespan


@pytest.mark.asyncio
async def test_database_manager_connects_once_and_disconnects(monkeypatch):
    client = MagicMock()
    database_handle = MagicMock()
    client.get_database.return_value = database_handle
    database_handle.__getitem__.return_value.create_indexes = AsyncMock()
    client_class = MagicMock(return_value=client)
    monkeypatch.setattr(database_module, "AsyncIOMotorClient", client_class)

    manager = DatabaseManager()

    first_database = await manager.get_db()
    second_database = await manager.get_db()

    assert first_database is database_handle
    assert second_database is database_handle
    client_class.assert_called_once_with(database_module.settings.database_url)
    client.get_database.assert_called_once_with(database_module.DATABASE_NAME)
    assert database_handle.__getitem__.call_count == len(
        database_module.COLLECTION_NAMES
    )
    assert database_handle.__getitem__.return_value.create_indexes.await_count == len(
        database_module.COLLECTION_NAMES
    )

    await manager.disconnect()

    client.close.assert_called_once_with()
    assert manager.client is None
    assert manager.db is None


@pytest.mark.asyncio
async def test_lifespan_connects_and_disconnects(monkeypatch):
    connect = AsyncMock()
    disconnect = AsyncMock()
    monkeypatch.setattr(database_module.database, "connect", connect)
    monkeypatch.setattr(database_module.database, "disconnect", disconnect)

    async with lifespan(MagicMock()):
        connect.assert_awaited_once_with()
        disconnect.assert_not_awaited()

    disconnect.assert_awaited_once_with()

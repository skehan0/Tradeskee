from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, IndexModel

from src.core.config import settings
from src.feature.logging import StdoutLoggingService, build_app_logger

# Initialize logger
logger = build_app_logger(handlers=[StdoutLoggingService()])

DATABASE_NAME = settings.MONGODB_DB_NAME
COLLECTION_NAMES = {
    "stock_metadata",
    "historical_data",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "earnings",
}


class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Establish a connection to MongoDB."""
        if self.client is None:
            try:
                logger.info("Connecting to MongoDB: %s", DATABASE_NAME)
                self.client = AsyncIOMotorClient(settings.database_url)
                self.db = self.client.get_database(DATABASE_NAME)
                logger.info("MongoDB connection established: %s", DATABASE_NAME)
                await self.ensure_indexes()
            except Exception as e:
                logger.error("MongoDB connection failed: %s", e)
                if self.client is not None:
                    self.client.close()
                self.client = None
                self.db = None
                raise e

    async def disconnect(self):
        """Close the database connection."""
        if self.client:
            logger.info("Closing MongoDB connection: %s", DATABASE_NAME)
            self.client.close()
            self.client = None
            self.db = None

    async def ensure_indexes(self):
        """Create indexes required by the stock-data repositories."""
        if self.db is None:
            raise RuntimeError("MongoDB connection is not established")

        indexes = [
            IndexModel([("ticker", ASCENDING)], name="ticker_idx"),
            IndexModel([("last_updated", ASCENDING)], name="last_updated_idx"),
        ]
        for collection_name in COLLECTION_NAMES:
            await self.db[collection_name].create_indexes(indexes)
        logger.info("MongoDB indexes ensured for %s collections", len(COLLECTION_NAMES))

    async def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        await self.connect()
        return self.db[collection_name]

    async def get_db(self):
        """Get the database instance."""
        await self.connect()
        return self.db


# Create an instance of DatabaseManager
database = DatabaseManager()

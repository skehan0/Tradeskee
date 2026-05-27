import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from src.feature.logging import build_app_logger, StdoutLoggingService

load_dotenv()

# Initialize logger
logger = build_app_logger(handlers=[StdoutLoggingService()])

DATABASE_NAME = "tradely"
COLLECTION_NAMES = {'historical_data', 'stock_metadata'}

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Establish a connection to MongoDB."""
        if self.client is None:
            MONGO_URI = os.getenv("MONGO_URI")
            if not MONGO_URI:
                logger.error("MongoDB connection failed: MONGO_URI not set")
                raise ValueError("MONGO_URI environment variable is not set.")

            try:
                logger.info("Connecting to MongoDB", database=DATABASE_NAME)
                print("Connecting to MongoDB...")
                self.client = AsyncIOMotorClient(MONGO_URI)
                self.db = self.client[DATABASE_NAME]
                logger.info("MongoDB connection established", database=DATABASE_NAME)
                print("Successfully connected to MongoDB!")
            except Exception as e:
                logger.error("MongoDB connection failed", error=str(e))
                print(f"Error connecting to MongoDB: {e}")
                raise e

    async def disconnect(self):
        """Close the database connection."""
        if self.client:
            logger.info("Closing MongoDB connection", database=DATABASE_NAME)
            self.client.close()
            self.client = None
            self.db = None
            print("MongoDB connection closed.")

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
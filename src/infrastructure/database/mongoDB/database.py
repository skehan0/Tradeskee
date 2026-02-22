import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

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
                raise ValueError("MONGO_URI environment variable is not set.")

            try:
                print("Connecting to MongoDB...")
                self.client = AsyncIOMotorClient(MONGO_URI)
                self.db = self.client[DATABASE_NAME]
                print("Successfully connected to MongoDB!")
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                raise e

    async def disconnect(self):
        """Close the database connection."""
        if self.client:
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
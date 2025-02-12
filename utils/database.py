from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from utils.config import Config
from utils.logger import logger


class MongoDB:
    def __init__(self):
        self.config = Config()
        self.uri: str = self.config.mongodb_uri
        self.client = None
        self.database = {}

    async def connect(self):
        # Create the client with a server selection timeout
        self.client = AsyncIOMotorClient(self.uri, serverSelectionTimeoutMS=5000)
        try:
            # Perform a ping to quickly verify the connection
            await self.client.admin.command("ping")
        except Exception as e:
            raise ConnectionFailure(f"Could not connect to MongoDB at {self.uri}: {e}")

        for db_name in self.config.mongodb_dbs:
            self.database[db_name] = self.client[db_name]

        logger.debug("Connected to MongoDB")

    def get_database(self, db_name: str):
        return self.database[db_name]

    async def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None

mongodb = MongoDB()

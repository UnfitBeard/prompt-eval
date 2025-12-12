# core/database.py
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
import logging

from config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            # Prefer config-backed settings (reads .env), fall back to environment for compatibility.
            mongo_uri = settings.MONGO_DB_URI or os.getenv("MONGO_DB_URI")
            if not mongo_uri:
                raise ValueError("MONGO_DB_URI is required")

            self.client = AsyncIOMotorClient(
                mongo_uri,
                maxPoolSize=100,
                minPoolSize=10,
                retryWrites=True,
            )

            # Test connection
            await self.client.admin.command("ping")
            self.db = self.client.get_database(settings.MONGO_DB_NAME)

            logger.info("Connected to MongoDB successfully")
            await self.create_indexes()

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise

    async def create_indexes(self):
        """Create necessary indexes"""
        # Users collection indexes
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index([("xp", -1)])  # For leaderboards

        # Courses collection indexes
        await self.db.courses.create_index("slug", unique=True)
        await self.db.courses.create_index([("published", 1), ("difficulty", 1)])

        # User progress indexes
        await self.db.user_progress.create_index([("user_id", 1), ("course_id", 1)], unique=True)
        await self.db.user_progress.create_index([("user_id", 1), ("completed", 1)])

        # Lesson attempts indexes
        await self.db.lesson_attempts.create_index([("user_id", 1), ("lesson_id", 1), ("created_at", -1)])

        logger.info("Database indexes created")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")


# Singleton instance
mongodb = MongoDB()

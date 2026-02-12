# core/database.py
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, OperationFailure
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

    async def _ensure_courses_slug_index(self):
        """Ensure `courses.slug` has the expected partial unique index.

        We currently want a *partial* unique index so we enforce uniqueness for real
        string slugs while allowing documents that don't have `slug` (or have non-string
        values like null) to coexist.

        Older deployments may already have a non-partial unique index auto-named
        `slug_1`, which will conflict with attempts to create the new partial index.
        """

        desired_partial = {"slug": {"$type": "string"}}

        existing = None
        async for idx in self.db.courses.list_indexes():
            if idx.get("key") == {"slug": 1}:
                existing = idx
                break

        # If an index exists on slug but doesn't match our desired shape, rebuild it.
        if existing:
            if (
                existing.get("unique") is True
                and existing.get("partialFilterExpression") == desired_partial
            ):
                return

            name = existing.get("name")
            if name:
                logger.warning(
                    "Rebuilding courses.slug index (dropping %s, recreating partial unique)",
                    name,
                )
                try:
                    await self.db.courses.drop_index(name)
                except OperationFailure as e:
                    # If we can't drop it (permissions, etc.), surface the original issue
                    # rather than failing later with a less clear conflict.
                    logger.error("Failed to drop conflicting index %s: %s", name, e)
                    raise

        # Use an explicit name to keep this stable across environments.
        await self.db.courses.create_index(
            [("slug", 1)],
            name="slug_1",
            unique=True,
            partialFilterExpression=desired_partial,
        )

    async def _ensure_users_unique_string_index(self, field: str):
        """Ensure users.<field> is a partial unique index for string values.

        Mongo unique indexes treat `null` as a value, so multiple legacy documents with
        `{field: null}` (or `{field: None}`) will prevent the unique index from building.

        We use a partial index to enforce uniqueness only for real string values.
        """

        desired_partial = {field: {"$type": "string"}}

        existing = None
        async for idx in self.db.users.list_indexes():
            if idx.get("key") == {field: 1}:
                existing = idx
                break

        if existing:
            if (
                existing.get("unique") is True
                and existing.get("partialFilterExpression") == desired_partial
            ):
                return

            name = existing.get("name")
            if name:
                logger.warning(
                    "Rebuilding users.%s index (dropping %s, recreating partial unique)",
                    field,
                    name,
                )
                try:
                    await self.db.users.drop_index(name)
                except OperationFailure as e:
                    logger.error("Failed to drop conflicting index %s: %s", name, e)
                    raise

        await self.db.users.create_index(
            [(field, 1)],
            name=f"{field}_1",
            unique=True,
            partialFilterExpression=desired_partial,
        )

    async def create_indexes(self):
        """Create necessary indexes"""
        # Users collection indexes
        await self._ensure_users_unique_string_index("email")
        await self._ensure_users_unique_string_index("username")
        await self.db.users.create_index([("xp", -1)])  # For leaderboards

        # Courses collection indexes
        #
        # This repo uses the `courses` collection for two different shapes:
        # 1) "Academy" courses (id: basics/rag/advanced, modules, etc.)
        # 2) "Catalog" courses (slug, status, total_duration, etc.)
        await self._ensure_courses_slug_index()

        # Index for catalog queries.
        await self.db.courses.create_index([("status", 1), ("difficulty", 1)])
        # Index for academy lookups by stable string id (basics/rag/advanced).
        await self.db.courses.create_index("id")

        # User progress indexes
        await self.db.user_progress.create_index(
            [("user_id", 1), ("course_id", 1)],
            unique=True,
        )
        await self.db.user_progress.create_index([("user_id", 1), ("completed", 1)])

        # Lesson attempts indexes
        await self.db.lesson_attempts.create_index(
            [("user_id", 1), ("lesson_id", 1), ("created_at", -1)]
        )

        # Prompt scores indexes
        await self.db.prompt_scores.create_index([("user_id", 1), ("timestamp", -1)])
        await self.db.prompt_scores.create_index([("user_id", 1)])

        # Templates indexes
        await self.db.templates.create_index([("domain", 1), ("category", 1)])
        await self.db.templates.create_index([("status", 1)])
        await self.db.templates.create_index([("createdBy", 1)])

        logger.info("Database indexes created")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")


# Singleton instance
mongodb = MongoDB()

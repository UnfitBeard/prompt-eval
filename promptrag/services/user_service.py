# services/user_service.py
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from core.database import mongodb
from core.password import get_password_hash, verify_password
from models.user import UserCreate, UserInDB, UserPublic, UserRole, UserLevel
from schemas.user import UserCreateSchema, UserUpdateSchema

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        # Don't touch mongodb.db at import time.
        self.collection = None

    async def any_admin_exists(self) -> bool:
        """Return True if at least one admin user exists."""
        await self._ensure_connected()
        return (
            await self.collection.count_documents({"role": UserRole.ADMIN.value})
        ) > 0

    async def _ensure_connected(self):
        if mongodb.db is None:
            await mongodb.connect()

        if self.collection is None:
            self.collection = mongodb.db.users

    async def _create_user_with_role(
        self,
        user_data: UserCreateSchema,
        role: UserRole,
    ) -> UserInDB:
        """Internal helper to create a user with a specific role."""
        await self._ensure_connected()

        # Check if user exists
        existing_user = await self.collection.find_one({
            "$or": [
                {"email": user_data.email},
                {"username": user_data.username}
            ]
        })

        if existing_user:
            if existing_user["email"] == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")

        # Create user document
        user_dict = user_data.dict(exclude={"password"})
        user_dict.update({
            "hashed_password": get_password_hash(user_data.password),
            "role": role.value,
            "level": UserLevel.BEGINNER.value,
            "xp": 0,
            "streak_days": 0,
            "last_active": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "email_verified": False,
            "is_active": True
        })

        # Insert into database
        result = await self.collection.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)

        return UserInDB(**user_dict)

    async def create_user(self, user_data: UserCreateSchema) -> UserInDB:
        """Create a new student user"""
        return await self._create_user_with_role(user_data, UserRole.STUDENT)

    async def create_admin_user(self, user_data: UserCreateSchema) -> UserInDB:
        """Create a new admin user"""
        return await self._create_user_with_role(user_data, UserRole.ADMIN)

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user"""
        await self._ensure_connected()

        user = await self.collection.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })

        if not user:
            return None

        if not verify_password(password, user["hashed_password"]):
            return None

        # Update last active
        await self.collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )

        # Check and update streak
        await self._update_streak(user["_id"])

        user["id"] = str(user["_id"])
        return UserInDB(**user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        await self._ensure_connected()
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                return UserInDB(**user)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        await self._ensure_connected()
        user = await self.collection.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            return UserInDB(**user)
        return None

    async def update_user(self, user_id: str, update_data: UserUpdateSchema) -> Optional[UserInDB]:
        """Update user profile"""
        await self._ensure_connected()

        update_dict = {k: v for k, v in update_data.dict(
            exclude_unset=True).items() if v is not None}

        if not update_dict:
            return await self.get_user_by_id(user_id)

        update_dict["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )

        return await self.get_user_by_id(user_id)

    async def add_xp(self, user_id: str, xp_amount: int) -> bool:
        """Add XP to user and update level"""
        await self._ensure_connected()
        try:
            # Update XP
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"xp": xp_amount}}
            )

            if result.modified_count > 0:
                # Check for level up
                await self._check_level_up(user_id)
                return True

            return False
        except Exception as e:
            logger.error(f"Error adding XP to user {user_id}: {e}")
            return False

    async def _update_streak(self, user_id: ObjectId):
        """Update user's streak days"""
        user = await self.collection.find_one({"_id": user_id})
        if not user:
            return

        last_active = user.get("last_active", datetime.utcnow())
        now = datetime.utcnow()

        # If last active was yesterday or today, continue streak
        if (now - last_active).days <= 1:
            # If last active was yesterday, increment streak
            if (now - last_active).days == 1:
                await self.collection.update_one(
                    {"_id": user_id},
                    {"$inc": {"streak_days": 1}}
                )
        else:
            # Break streak
            await self.collection.update_one(
                {"_id": user_id},
                {"$set": {"streak_days": 1}}
            )

    async def _check_level_up(self, user_id: str):
        """Check if user should level up based on XP"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return

        xp_thresholds = {
            UserLevel.BEGINNER: 0,
            UserLevel.INTERMEDIATE: 1000,
            UserLevel.ADVANCED: 5000,
            UserLevel.EXPERT: 15000
        }

        current_level = user.level
        current_xp = user.xp

        # Determine new level
        new_level = current_level
        for level, threshold in sorted(xp_thresholds.items(), key=lambda x: x[1], reverse=True):
            if current_xp >= threshold:
                new_level = level
                break

        # Update if level changed
        if new_level != current_level:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"level": new_level.value}}
            )
            logger.info(f"User {user_id} leveled up to {new_level}")

    async def get_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get leaderboard sorted by XP"""
        await self._ensure_connected()
        cursor = self.collection.find(
            {"is_active": True},
            {"username": 1, "xp": 1, "level": 1, "streak_days": 1, "avatar_url": 1}
        ).sort("xp", -1).limit(limit)

        users = await cursor.to_list(length=limit)

        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": str(user["_id"]),
                "username": user["username"],
                "xp": user.get("xp", 0),
                "level": user.get("level", UserLevel.BEGINNER.value),
                "streak_days": user.get("streak_days", 0),
                "avatar_url": user.get("avatar_url")
            })

        return result

    # Add token creation methods here to avoid circular imports
    def create_tokens_for_user(self, user: UserInDB):
        """Create access and refresh tokens for a user"""
        from core.security import create_access_token, create_refresh_token

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        return access_token, refresh_token

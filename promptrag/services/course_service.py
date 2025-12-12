# services/course_service.py - FIXED VERSION
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

from core.database import mongodb
from models.course import CourseCreate, CourseInDB, CourseStatus, CoursePublic

logger = logging.getLogger(__name__)


class CourseService:
    def __init__(self):
        self._collection = None
        self._progress_collection = None
        self._db = None

    async def _ensure_connected(self):
        """Ensure MongoDB connection is established"""
        if self._db is None:
            try:
                # Connect to MongoDB
                await mongodb.connect()
                self._db = mongodb.db
                self._collection = self._db.courses
                self._progress_collection = self._db.user_progress
                logger.info("MongoDB connection established for CourseService")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

    @property
    async def collection(self):
        """Get courses collection with lazy loading"""
        if self._collection is None:
            await self._ensure_connected()
        return self._collection

    @property
    async def progress_collection(self):
        """Get progress collection with lazy loading"""
        if self._progress_collection is None:
            await self._ensure_connected()
        return self._progress_collection

    async def get_courses(
        self,
        difficulty: Optional[str] = None,
        status: str = CourseStatus.PUBLISHED.value,
        limit: int = 20,
        skip: int = 0,
        user_id: Optional[str] = None
    ) -> List[CoursePublic]:
        """Get courses with filters"""
        try:
            # Get collections
            collection = await self.collection

            query = {"status": status}
            if difficulty:
                query["difficulty"] = difficulty

            # Get courses
            cursor = collection.find(query).sort(
                "created_at", -1).skip(skip).limit(limit)
            courses = await cursor.to_list(length=limit)

            if not courses:
                return []

            # Get user progress if user_id provided
            user_progress = {}
            if user_id:
                progress_col = await self.progress_collection
                progress_cursor = progress_col.find({"user_id": user_id})
                user_progress_list = await progress_cursor.to_list(length=None)
                user_progress = {p["course_id"]: p for p in user_progress_list}

            # Get instructor names
            instructor_ids = list(set([c["instructor_id"] for c in courses]))
            instructor_map = {}

            if instructor_ids:
                instructors_cursor = self._db.users.find(
                    {"_id": {
                        "$in": [ObjectId(id) for id in instructor_ids if ObjectId.is_valid(id)]}},
                    {"_id": 1, "full_name": 1}
                )
                instructors = await instructors_cursor.to_list(length=None)
                instructor_map = {str(instr["_id"]): instr.get("full_name", "Unknown")
                                  for instr in instructors}

            result = []
            for course in courses:
                course_data = self._convert_id(course)

                # Add instructor name
                course_data["instructor_name"] = instructor_map.get(
                    course["instructor_id"], "Unknown")

                # Add progress if user has it
                if user_id and course_data["id"] in user_progress:
                    progress = user_progress[course_data["id"]]
                    total_lessons = course_data.get("total_lessons", 1)
                    completed = len(progress.get("completed_lessons", []))
                    course_data["progress_percentage"] = (
                        completed / total_lessons) * 100 if total_lessons > 0 else 0

                result.append(CoursePublic(**course_data))

            return result
        except Exception as e:
            logger.error(f"Error getting courses: {e}", exc_info=True)
            raise

    async def get_course(self, course_id: str, user_id: Optional[str] = None) -> Optional[CoursePublic]:
        """Get course by ID with optional user progress"""
        try:
            collection = await self.collection

            if not ObjectId.is_valid(course_id):
                return None

            course = await collection.find_one({"_id": ObjectId(course_id)})
            if not course:
                return None

            # Get instructor name
            instructor = await self._db.users.find_one(
                {"_id": ObjectId(course["instructor_id"])},
                {"full_name": 1}
            )

            course_data = self._convert_id(course)
            course_data["instructor_name"] = instructor.get(
                "full_name", "Unknown") if instructor else "Unknown"

            # Get user progress if user_id provided
            if user_id:
                progress_col = await self.progress_collection
                progress = await progress_col.find_one({
                    "user_id": user_id,
                    "course_id": course_id
                })
                if progress:
                    total_lessons = course_data.get("total_lessons", 1)
                    completed = len(progress.get("completed_lessons", []))
                    course_data["progress_percentage"] = (
                        completed / total_lessons) * 100 if total_lessons > 0 else 0

            return CoursePublic(**course_data)
        except Exception as e:
            logger.error(f"Error getting course {course_id}: {e}")
            return None

    async def count_courses(self, difficulty: Optional[str] = None) -> int:
        """Count total published courses"""
        try:
            collection = await self.collection

            query = {"status": CourseStatus.PUBLISHED.value}
            if difficulty:
                query["difficulty"] = difficulty

            return await collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting courses: {e}")
            return 0

    async def create_course(self, course: CourseCreate, instructor: Any) -> CourseInDB:
        """Create a new course"""
        try:
            collection = await self.collection

            # Check if slug already exists
            existing = await collection.find_one({"slug": course.slug})
            if existing:
                raise ValueError(
                    f"Course with slug '{course.slug}' already exists")

            course_dict = course.dict()
            course_dict.update({
                "instructor_id": str(instructor.id),
                "status": CourseStatus.DRAFT.value,
                "total_lessons": 0,
                "enrolled_count": 0,
                "review_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "lesson_order": []
            })

            result = await collection.insert_one(course_dict)
            course_dict["id"] = str(result.inserted_id)

            return CourseInDB(**course_dict)
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            raise

    async def enroll_user(self, course_id: str, user_id: str) -> bool:
        """Enroll user in a course"""
        try:
            collection = await self.collection
            progress_col = await self.progress_collection

            # Check if already enrolled
            existing = await progress_col.find_one({
                "user_id": user_id,
                "course_id": course_id
            })

            if existing:
                return True  # Already enrolled

            # Create progress record
            progress = {
                "user_id": user_id,
                "course_id": course_id,
                "current_lesson_id": None,
                "completed_lessons": [],
                "total_xp_earned": 0,
                "started_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "completed": False
            }

            await progress_col.insert_one(progress)

            # Increment enrolled count
            await collection.update_one(
                {"_id": ObjectId(course_id)},
                {"$inc": {"enrolled_count": 1}}
            )

            return True
        except Exception as e:
            logger.error(
                f"Error enrolling user {user_id} in course {course_id}: {e}")
            return False

    def _convert_id(self, doc: Dict) -> Dict:
        """Convert MongoDB _id to id"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc

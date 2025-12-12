# services/progress_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from core.database import mongodb
from models.progress import UserProgressBase, LessonAttempt
from schemas.progress import CourseProgressSchema, UserProgressSummarySchema

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self):
        # Don't touch mongodb.db at import time.
        self.progress_collection = None
        self.attempts_collection = None
        self.users_collection = None
        self.courses_collection = None

    async def _ensure_connected(self):
        if mongodb.db is None:
            await mongodb.connect()

        if self.progress_collection is None:
            self.progress_collection = mongodb.db.user_progress
            self.attempts_collection = mongodb.db.lesson_attempts
            self.users_collection = mongodb.db.users
            self.courses_collection = mongodb.db.courses

    async def get_user_progress_summary(self, user_id: str) -> UserProgressSummarySchema:
        """Get comprehensive progress summary for a user"""
        await self._ensure_connected()

        # Get user info
        user = await self.users_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"xp": 1, "level": 1, "streak_days": 1}
        )

        if not user:
            raise ValueError("User not found")

        # Get all enrolled courses with progress
        cursor = self.progress_collection.find({"user_id": user_id})
        progress_list = await cursor.to_list(length=None)

        enrolled_courses = []
        for progress in progress_list:
            course = await self.courses_collection.find_one(
                {"_id": ObjectId(progress["course_id"])},
                {"title": 1, "total_lessons": 1}
            )

            if course:
                completed_lessons = len(progress.get("completed_lessons", []))
                total_lessons = course.get("total_lessons", 1)

                enrolled_courses.append(CourseProgressSchema(
                    course_id=progress["course_id"],
                    course_title=course.get("title", "Unknown"),
                    completed_lessons=completed_lessons,
                    total_lessons=total_lessons,
                    progress_percentage=(
                        completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0,
                    total_xp_earned=progress.get("total_xp_earned", 0),
                    current_lesson_id=progress.get("current_lesson_id"),
                    started_at=progress.get("started_at"),
                    last_accessed=progress.get("last_accessed")
                ))

        # Count completed courses
        completed_courses = sum(
            1 for course in enrolled_courses
            if course.progress_percentage >= 100
        )

        return UserProgressSummarySchema(
            user_id=user_id,
            total_courses=len(enrolled_courses),
            completed_courses=completed_courses,
            total_xp=user.get("xp", 0),
            level=user.get("level", "beginner"),
            streak_days=user.get("streak_days", 0),
            enrolled_courses=enrolled_courses
        )

    async def get_recent_activity(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's recent learning activity"""
        await self._ensure_connected()

        # Get recent lesson attempts
        attempts = await self.attempts_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        activity = []
        for attempt in attempts:
            # Get lesson details
            lesson = await mongodb.db.lessons.find_one(
                {"_id": ObjectId(attempt["lesson_id"])},
                {"title": 1, "course_id": 1}
            )

            # Get course details
            course = await self.courses_collection.find_one(
                {"_id": ObjectId(attempt["course_id"])},
                {"title": 1}
            )

            activity.append({
                "type": "lesson_attempt",
                "lesson_id": attempt["lesson_id"],
                "lesson_title": lesson.get("title", "Unknown") if lesson else "Unknown",
                "course_id": attempt["course_id"],
                "course_title": course.get("title", "Unknown") if course else "Unknown",
                "xp_earned": attempt.get("xp_earned", 0),
                "status": attempt.get("status"),
                "created_at": attempt.get("created_at"),
                "time_spent": attempt.get("time_spent_seconds", 0)
            })

        return activity

    async def get_streak_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's learning streak data"""
        await self._ensure_connected()
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all attempts in the date range
        attempts = await self.attempts_collection.find({
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=None)

        # Group by day
        daily_activity = {}
        for attempt in attempts:
            day = attempt["created_at"].strftime("%Y-%m-%d")
            if day not in daily_activity:
                daily_activity[day] = {
                    "date": day,
                    "attempts": 0,
                    "xp_earned": 0,
                    "lessons_completed": 0
                }

            daily_activity[day]["attempts"] += 1
            daily_activity[day]["xp_earned"] += attempt.get("xp_earned", 0)

            if attempt.get("status") == "correct":
                daily_activity[day]["lessons_completed"] += 1

        # Create full date range
        date_range = []
        for i in range(days + 1):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            activity = daily_activity.get(date, {
                "date": date,
                "attempts": 0,
                "xp_earned": 0,
                "lessons_completed": 0
            })
            date_range.append(activity)

        date_range.reverse()  # Oldest to newest

        # Calculate current streak
        current_streak = 0
        today = end_date.strftime("%Y-%m-%d")
        yesterday = (end_date - timedelta(days=1)).strftime("%Y-%m-%d")

        if today in daily_activity and daily_activity[today]["attempts"] > 0:
            current_streak += 1

        # Check previous days
        for i in range(1, days):
            check_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if check_date in daily_activity and daily_activity[check_date]["attempts"] > 0:
                current_streak += 1
            else:
                break

        return {
            "current_streak": current_streak,
            "max_streak": await self._calculate_max_streak(user_id),
            "daily_activity": date_range,
            "total_attempts": len(attempts),
            "total_xp": sum(a.get("xp_earned", 0) for a in attempts)
        }

    async def _calculate_max_streak(self, user_id: str) -> int:
        """Calculate user's maximum streak"""
        # Get all attempts sorted by date
        attempts = await self.attempts_collection.find(
            {"user_id": user_id}
        ).sort("created_at", 1).to_list(length=None)

        if not attempts:
            return 0

        # Extract unique dates
        dates = sorted(set(a["created_at"].strftime("%Y-%m-%d")
                       for a in attempts))

        # Calculate streaks
        max_streak = 0
        current_streak = 1

        for i in range(1, len(dates)):
            prev_date = datetime.strptime(dates[i-1], "%Y-%m-%d")
            curr_date = datetime.strptime(dates[i], "%Y-%m-%d")

            if (curr_date - prev_date).days == 1:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1

        return max(max_streak, current_streak)

    async def get_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's achievements and progress"""
        await self._ensure_connected()

        achievements = [
            {
                "id": "first_lesson",
                "name": "First Steps",
                "description": "Complete your first lesson",
                "icon": "🎯",
                "xp_reward": 50,
                "condition": lambda user, progress: len(progress.get("completed_lessons", [])) >= 1
            },
            {
                "id": "streak_7",
                "name": "Week Warrior",
                "description": "Maintain a 7-day learning streak",
                "icon": "🔥",
                "xp_reward": 100,
                "condition": lambda user, progress: user.get("streak_days", 0) >= 7
            },
            {
                "id": "xp_1000",
                "name": "Knowledge Seeker",
                "description": "Earn 1000 XP",
                "icon": "🏆",
                "xp_reward": 200,
                "condition": lambda user, progress: user.get("xp", 0) >= 1000
            },
            {
                "id": "complete_course",
                "name": "Course Conqueror",
                "description": "Complete your first course",
                "icon": "🎓",
                "xp_reward": 300,
                "condition": lambda user, progress: progress.get("completed_courses", 0) >= 1
            },
            {
                "id": "perfect_score",
                "name": "Perfectionist",
                "description": "Get a perfect score on 10 lessons",
                "icon": "💯",
                "xp_reward": 150,
                "condition": lambda user, progress: self._count_perfect_lessons(user_id) >= 10
            }
        ]

        user = await self.users_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"xp": 1, "streak_days": 1, "level": 1}
        )

        progress_summary = await self.get_user_progress_summary(user_id)

        result = []
        for achievement in achievements:
            earned = achievement["condition"](
                user or {}, progress_summary.dict())

            # Check if already earned
            earned_record = await mongodb.db.user_achievements.find_one({
                "user_id": user_id,
                "achievement_id": achievement["id"]
            })

            result.append({
                **achievement,
                "earned": earned or bool(earned_record),
                "earned_at": earned_record.get("earned_at") if earned_record else None,
                "progress": self._calculate_achievement_progress(achievement["id"], user, progress_summary)
            })

        return result

    async def _count_perfect_lessons(self, user_id: str) -> int:
        """Count lessons where user got perfect score"""
        perfect_attempts = await self.attempts_collection.count_documents({
            "user_id": user_id,
            "status": "correct"
        })
        return perfect_attempts

    def _calculate_achievement_progress(self, achievement_id: str, user: Dict, progress) -> Optional[float]:
        """Calculate progress for progressive achievements"""
        if achievement_id == "perfect_score":
            perfect_count = self._count_perfect_lessons(user["_id"])
            return min(perfect_count / 10, 1.0)

        return None

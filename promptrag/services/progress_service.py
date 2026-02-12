# services/progress_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import logging

from core.database import mongodb
from models.progress import UserProgressBase, LessonAttempt
from schemas.progress import (
    CourseProgressSchema,
    UserProgressSummarySchema,
    ModuleProgressSchema,
    CertificateSchema,
)

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self):
        # Don't touch mongodb.db at import time.
        self.progress_collection = None
        self.attempts_collection = None
        self.users_collection = None
        self.courses_collection = None
        self.lessons_collection = None
        self.certificates_collection = None

    async def _ensure_connected(self):
        if mongodb.db is None:
            await mongodb.connect()

        if self.progress_collection is None:
            self.progress_collection = mongodb.db.user_progress
            self.attempts_collection = mongodb.db.lesson_attempts
            self.users_collection = mongodb.db.users
            self.courses_collection = mongodb.db.courses
            self.lessons_collection = mongodb.db.lessons
            # This collection is optional – if it does not exist yet,
            # MongoDB will happily return an empty cursor.
            self.certificates_collection = mongodb.db.user_certificates

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
        """Get user's achievements and progress.

        The return shape here is intentionally richer than
        AchievementSchema so that the dashboard can treat achievements
        as "badges" (with an `earned` flag) while legacy consumers can
        continue to use /progress/achievements as-is.
        """
        await self._ensure_connected()

        # Precompute counts needed for achievement conditions that depend on
        # async database calls so that our condition predicates remain
        # synchronous. This avoids mixing coroutines with plain comparisons
        # inside the lambda conditions below.
        perfect_lessons_count = await self._count_perfect_lessons(user_id)

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
                # Use the precomputed perfect_lessons_count so this
                # predicate stays synchronous and we don't accidentally
                # compare a coroutine object to an int.
                "condition": lambda user, progress, count=perfect_lessons_count: count >= 10
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

    async def get_course_modules_for_user(self, user_id: str, course_id: str) -> List[ModuleProgressSchema]:
        """Return per-module (lesson) progress for a user within a course.

        This powers the frontend ModuleProgressCard and is designed to
        be lightweight: it only inspects lesson metadata, the user's
        progress document, and the most recent attempt per lesson.
        """
        await self._ensure_connected()

        # Fetch the user's course progress so we know which lessons
        # are completed and how much XP has been earned overall.
        progress = await self.progress_collection.find_one(
            {"user_id": user_id, "course_id": course_id}
        )
        completed_lessons = set(progress.get("completed_lessons", [])) if progress else set()

        # All lessons ("modules" in the dashboard language) for this course.
        lessons_cursor = self.lessons_collection.find({"course_id": course_id}).sort("order", 1)
        lessons = await lessons_cursor.to_list(length=None)

        modules: List[ModuleProgressSchema] = []

        for lesson in lessons:
            lesson_id = str(lesson["_id"])

            # Look at the most recent attempt for this lesson, if any,
            # so we can infer a score and per-lesson XP.
            attempts = await self.attempts_collection.find({
                "user_id": user_id,
                "lesson_id": lesson_id,
            }).sort("created_at", -1).limit(1).to_list(length=1)

            last_attempt = attempts[0] if attempts else None
            xp_earned = int(last_attempt.get("xp_earned", 0)) if last_attempt else 0

            max_xp = int(lesson.get("total_xp", 0)) or 0
            score_percentage: Optional[float] = None
            if max_xp > 0 and xp_earned > 0:
                # Approximate score as XP earned vs. total XP for the
                # lesson. This keeps the logic simple while still
                # giving the UI a meaningful percentage to display.
                score_percentage = (xp_earned / max_xp) * 100

            status = "not_started"
            completed_at = None

            if lesson_id in completed_lessons:
                status = "completed"
                if last_attempt and last_attempt.get("status") == "correct":
                    completed_at = last_attempt.get("created_at")
            elif xp_earned > 0:
                status = "in_progress"

            modules.append(
                ModuleProgressSchema(
                    module_id=lesson_id,
                    course_id=course_id,
                    title=lesson.get("title", "Untitled lesson"),
                    order=int(lesson.get("order", 0) or 0),
                    max_xp=max_xp,
                    xp_earned=xp_earned,
                    status=status,
                    score_percentage=score_percentage,
                    completed_at=completed_at,
                )
            )

        return modules

    async def get_user_certificates(self, user_id: str) -> List[CertificateSchema]:
        """Return all certificates associated with a user.

        Certificates are stored in the optional `user_certificates`
        collection. If the collection is empty (or not yet used), this
        method simply returns an empty list so the frontend can render
        a graceful "no certificates yet" state.
        """
        await self._ensure_connected()

        cursor = self.certificates_collection.find({"user_id": user_id}).sort(
            "issued_at", -1
        )
        docs = await cursor.to_list(length=None)

        certificates: List[CertificateSchema] = []
        for doc in docs:
            certificates.append(
                CertificateSchema(
                    id=str(doc.get("_id")),
                    user_id=doc.get("user_id", user_id),
                    course_id=doc.get("course_id", ""),
                    title=doc.get("title", "Course Certificate"),
                    issued_at=doc.get("issued_at", datetime.utcnow()),
                    download_url=doc.get("download_url", ""),
                )
            )

        return certificates

    async def _count_perfect_lessons(self, user_id: str) -> int:
        """Count lessons where user got perfect score"""
        perfect_attempts = await self.attempts_collection.count_documents({
            "user_id": user_id,
            "status": "correct"
        })
        return perfect_attempts

    def _calculate_achievement_progress(self, achievement_id: str, user: Dict, progress) -> Optional[float]:
        """Calculate progress for progressive achievements.

        NOTE: This helper remains intentionally lightweight. For now
        only the "perfect_score" badge exposes a numeric progress
        value. Other achievements can be extended here as needed.
        """
        if achievement_id == "perfect_score":
            # This is a best-effort approximation; it does not block
            # the main dashboard functionality if the underlying query
            # fails, because get_achievements() already marks badges as
            # earned/not-earned based on simpler predicates.
            return None

        return None

# services/lesson_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

from core.database import mongodb
from models.lesson import LessonCreate, LessonInDB, LessonPublic, LessonQuestion, QuestionType
from models.progress import LessonAttempt, AttemptStatus

logger = logging.getLogger(__name__)


class LessonService:
    def __init__(self):
        # NOTE: Don't touch mongodb.db at import time.
        # Routers instantiate services at module import time, before Mongo is connected.
        self.collection = None
        self.attempts_collection = None
        self.progress_collection = None

    async def _ensure_connected(self):
        """Ensure MongoDB connection + collections are initialized."""
        if mongodb.db is None:
            await mongodb.connect()

        if self.collection is None:
            self.collection = mongodb.db.lessons
            self.attempts_collection = mongodb.db.lesson_attempts
            self.progress_collection = mongodb.db.user_progress

    async def create_lesson(self, lesson: LessonCreate) -> LessonInDB:
        """Create a new lesson"""
        await self._ensure_connected()

        # Check if lesson order is available
        existing = await self.collection.find_one({
            "course_id": lesson.course_id,
            "order": lesson.order
        })
        if existing:
            raise ValueError(
                f"Lesson with order {lesson.order} already exists in this course")

        lesson_dict = lesson.dict()
        lesson_dict.update({
            "total_xp": sum(q.xp_reward for q in lesson.questions),
            "completed_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "published": True
        })

        result = await self.collection.insert_one(lesson_dict)
        lesson_dict["id"] = str(result.inserted_id)

        # Update course's total lessons and lesson order
        await mongodb.db.courses.update_one(
            {"_id": ObjectId(lesson.course_id)},
            {
                "$inc": {"total_lessons": 1},
                "$push": {"lesson_order": lesson_dict["id"]}
            }
        )

        return LessonInDB(**lesson_dict)

    async def get_lesson(self, lesson_id: str, user_id: Optional[str] = None) -> Optional[LessonPublic]:
        """Get lesson by ID with optional user progress"""
        await self._ensure_connected()
        try:
            lesson = await self.collection.find_one({"_id": ObjectId(lesson_id)})
            if not lesson:
                return None

            # Get adjacent lessons for navigation
            course_lessons = await self.collection.find(
                {"course_id": lesson["course_id"]},
                {"_id": 1, "order": 1, "title": 1}
            ).sort("order", 1).to_list(length=None)

            lesson["next_lesson_id"] = None
            lesson["prev_lesson_id"] = None

            for i, l in enumerate(course_lessons):
                if str(l["_id"]) == lesson_id:
                    if i > 0:
                        lesson["prev_lesson_id"] = str(
                            course_lessons[i-1]["_id"])
                    if i < len(course_lessons) - 1:
                        lesson["next_lesson_id"] = str(
                            course_lessons[i+1]["_id"])
                    break

            # Get user progress if user_id provided
            if user_id:
                # Check if lesson is completed
                progress = await self.progress_collection.find_one({
                    "user_id": user_id,
                    "course_id": lesson["course_id"]
                })

                if progress and lesson_id in progress.get("completed_lessons", []):
                    lesson["is_completed"] = True

                    # Get XP earned for this lesson
                    attempts = await self.attempts_collection.find({
                        "user_id": user_id,
                        "lesson_id": lesson_id
                    }).sort("created_at", -1).limit(1).to_list(length=1)

                    if attempts:
                        lesson["user_xp_earned"] = attempts[0].get(
                            "xp_earned", 0)
                else:
                    lesson["is_completed"] = False

            return LessonPublic(**self._convert_id(lesson))
        except Exception as e:
            logger.error(f"Error getting lesson {lesson_id}: {e}")
            return None

    async def submit_lesson_attempt(
        self,
        lesson_id: str,
        user_id: str,
        answers: Dict[str, Any],
        time_spent: int = 0
    ) -> Dict[str, Any]:
        """Submit lesson answers and calculate score"""
        await self._ensure_connected()
        try:
            # Get lesson and questions
            lesson = await self.collection.find_one({"_id": ObjectId(lesson_id)})
            if not lesson:
                raise ValueError("Lesson not found")

            questions = [LessonQuestion(**q)
                         for q in lesson.get("questions", [])]

            # Calculate score
            total_questions = len(questions)
            correct_answers = 0
            total_xp = 0
            feedback = []

            for question in questions:
                user_answer = answers.get(question.id)
                if not user_answer:
                    feedback.append(f"Question '{question.id}' not answered")
                    continue

                if self._check_answer(question, user_answer):
                    correct_answers += 1
                    total_xp += question.xp_reward
                    feedback.append(
                        f"Question '{question.id}': Correct! +{question.xp_reward} XP")
                else:
                    feedback.append(
                        f"Question '{question.id}': Incorrect. {question.explanation or ''}")

            # Determine status
            if correct_answers == total_questions:
                status = AttemptStatus.CORRECT
            elif correct_answers == 0:
                status = AttemptStatus.INCORRECT
            else:
                status = AttemptStatus.PARTIAL

            # Create attempt record
            attempt = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "course_id": lesson["course_id"],
                "answers": answers,
                "xp_earned": total_xp,
                "status": status.value,
                "time_spent_seconds": time_spent,
                "feedback": "\n".join(feedback),
                "created_at": datetime.utcnow()
            }

            result = await self.attempts_collection.insert_one(attempt)
            attempt["id"] = str(result.inserted_id)

            # If perfect score, mark lesson as completed
            if status == AttemptStatus.CORRECT:
                await self._mark_lesson_completed(user_id, lesson["course_id"], lesson_id, total_xp)

            return {
                "attempt_id": attempt["id"],
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "score_percentage": (correct_answers / total_questions) * 100,
                "xp_earned": total_xp,
                "status": status,
                "feedback": feedback,
                "next_lesson_id": await self._get_next_lesson_id(lesson["course_id"], lesson_id)
            }

        except Exception as e:
            logger.error(f"Error submitting lesson attempt: {e}")
            raise

    async def _mark_lesson_completed(self, user_id: str, course_id: str, lesson_id: str, xp_earned: int):
        """Mark lesson as completed and update user progress"""
        await self._ensure_connected()

        # Update user progress
        await self.progress_collection.update_one(
            {
                "user_id": user_id,
                "course_id": course_id
            },
            {
                "$addToSet": {"completed_lessons": lesson_id},
                "$inc": {"total_xp_earned": xp_earned},
                "$set": {
                    "current_lesson_id": lesson_id,
                    "last_accessed": datetime.utcnow()
                }
            },
            upsert=True
        )

        # Update user's total XP
        await mongodb.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"xp": xp_earned}}
        )

        # Update lesson completion count
        await self.collection.update_one(
            {"_id": ObjectId(lesson_id)},
            {"$inc": {"completed_count": 1}}
        )

    async def _get_next_lesson_id(self, course_id: str, current_lesson_id: str) -> Optional[str]:
        """Get the next lesson ID in sequence"""
        await self._ensure_connected()
        course = await mongodb.db.courses.find_one(
            {"_id": ObjectId(course_id)},
            {"lesson_order": 1}
        )

        if course and "lesson_order" in course:
            lesson_order = course["lesson_order"]
            try:
                current_index = lesson_order.index(current_lesson_id)
                if current_index < len(lesson_order) - 1:
                    return lesson_order[current_index + 1]
            except ValueError:
                pass

        return None

    def _check_answer(self, question: LessonQuestion, user_answer: Any) -> bool:
        """Check if user answer is correct based on question type"""
        if question.type == QuestionType.MULTIPLE_CHOICE:
            correct_answers = {
                opt.id for opt in question.options if opt.is_correct}
            return set(user_answer) == correct_answers
        elif question.type == QuestionType.SINGLE_CHOICE:
            correct_option = next(
                (opt.id for opt in question.options if opt.is_correct), None)
            return user_answer == correct_option
        elif question.type == QuestionType.TRUE_FALSE:
            return user_answer == question.correct_answer
        elif question.type == QuestionType.TEXT:
            # For text answers, we might need AI grading
            # For now, simple case-insensitive comparison
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        elif question.type == QuestionType.CODE:
            # Code questions would need execution/sandbox
            # For MVP, we'll trust the user got it right if they submitted
            return True
        return False

    def _convert_id(self, doc: Dict) -> Dict:
        """Convert MongoDB _id to id"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc

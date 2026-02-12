"""Seed courses that were previously defined only in the Angular
frontend `course-list` component into MongoDB.

This script captures the *course-level* metadata (title, subtitle,
learning outcomes, etc.) for the three main tracks:

- Prompt Engineering Basics
- Prompt Engineering for RAG Systems
- Advanced Prompt Engineering

It intentionally does **not** try to recreate the full module/lesson
structure from the frontend (those can later be modeled as `lessons`
if needed). The goal is to move the course definitions' source of truth
from the Angular component into the backend.
"""

from datetime import datetime
from typing import List

from core.database import mongodb
from models.course import CourseStatus, CourseCategory


FRONTEND_COURSES = [
    {
        "title": "Prompt Engineering Basics",
        "slug": "prompt-engineering-basics",
        "description": (
            "Foundations for working effectively with large language models. "
            "People who are new to prompt engineering and want a practical, "
            "non-technical introduction."
        ),
        "short_description": "Foundations for working effectively with large language models.",
        "difficulty": "beginner",
        "category": "ai",
        "language": "english",
        "thumbnail_url": None,
        # Approximate from course-list: 6 hours, ~20 modules.
        "total_lessons": 20,
        "total_duration": 6.0,
        "xp_reward": 1000,
        "tags": [
            "prompt-engineering",
            "foundations",
            "llm",
        ],
        "learning_outcomes": [
            "Explain what an LLM is and how prompts influence its behavior.",
            "Compose clear, structured prompts for everyday tasks.",
            "Use examples and constraints to get more reliable outputs.",
            "Debug low-quality model responses using simple checklists.",
        ],
        "prerequisites": ["Basic computer skills"],
    },
    {
        "title": "Prompt Engineering for RAG Systems",
        "slug": "prompt-engineering-for-rag-systems",
        "description": (
            "Design prompts that work hand-in-hand with retrieval to deliver "
            "grounded, up-to-date answers in RAG pipelines."
        ),
        "short_description": (
            "Design prompts that work hand-in-hand with retrieval to deliver "
            "grounded, up-to-date answers."
        ),
        "difficulty": "intermediate",
        "category": "ai",
        "language": "english",
        "thumbnail_url": None,
        "total_lessons": 14,
        "total_duration": 7.0,
        "xp_reward": 1500,
        "tags": [
            "rag",
            "retrieval",
            "grounding",
        ],
        "learning_outcomes": [
            "Describe the core components of a RAG system and how prompts interact with each stage.",
            "Design prompts that drive better document retrieval and grounded answer generation.",
            "Apply patterns for citation, attribution, and refusal when information is missing.",
            "Evaluate and iterate on RAG prompts using qualitative and quantitative signals.",
        ],
        "prerequisites": ["Prompt Engineering Basics", "Some backend / data experience"],
    },
    {
        "title": "Advanced Prompt Engineering",
        "slug": "advanced-prompt-engineering",
        "description": (
            "Explore sophisticated prompting strategies for complex reasoning, tooling, "
            "and multi-step workflows."
        ),
        "short_description": "Sophisticated prompting for complex reasoning and orchestration.",
        "difficulty": "advanced",
        "category": "ai",
        "language": "english",
        "thumbnail_url": None,
        "total_lessons": 10,
        "total_duration": 8.0,
        "xp_reward": 2000,
        "tags": [
            "advanced",
            "chain-of-thought",
            "tools",
        ],
        "learning_outcomes": [
            "Design prompts for complex, multi-step reasoning tasks.",
            "Use reflection and self-correction to improve answer quality.",
            "Orchestrate chains of prompts that cooperate with tools and external systems.",
            "Know when advanced prompting helps—and when to simplify instead.",
        ],
        "prerequisites": [
            "Prompt Engineering Basics",
            "Experience using prompts in real workflows",
        ],
    },
]


async def seed_frontend_courses() -> List[str]:
    """Insert or update the three frontend-defined courses into MongoDB.

    Courses are upserted based on their `slug`, so running this multiple
    times will not create duplicates.
    """

    await mongodb.connect()
    db = mongodb.db
    courses_col = db.courses

    inserted_ids: List[str] = []

    for course in FRONTEND_COURSES:
        now = datetime.utcnow()

        existing = await courses_col.find_one({"slug": course["slug"]})

        doc = {
            "title": course["title"],
            "slug": course["slug"],
            "description": course["description"],
            "short_description": course["short_description"],
            "difficulty": course["difficulty"],
            "status": CourseStatus.PUBLISHED.value,
            "category": course["category"] or CourseCategory.AI.value,
            # We do not wire a real instructor here; "Unknown" will be shown
            # by the CourseService when no matching user is found.
            "instructor_id": "frontend-migrated",
            "language": course["language"],
            "thumbnail_url": course["thumbnail_url"],
            "total_lessons": course["total_lessons"],
            "total_duration": course["total_duration"],
            "enrolled_count": 0,
            "review_count": 0,
            "average_rating": 0.0,
            "xp_reward": course["xp_reward"],
            "tags": course["tags"],
            "learning_outcomes": course["learning_outcomes"],
            "prerequisites": course["prerequisites"],
            "price": 0.0,
            "updated_at": now,
        }

        if existing:
            await courses_col.update_one({"_id": existing["_id"]}, {"$set": doc})
            inserted_ids.append(str(existing["_id"]))
        else:
            doc["created_at"] = now
            doc["lesson_order"] = []
            result = await courses_col.insert_one(doc)
            inserted_ids.append(str(result.inserted_id))

    await mongodb.disconnect()
    return inserted_ids


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    import asyncio

    print("Seeding frontend-defined courses into MongoDB...")
    ids = asyncio.run(seed_frontend_courses())
    print("Done. Upserted course IDs:")
    for cid in ids:
        print(" -", cid)

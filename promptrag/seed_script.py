# scripts/seed_courses.py
from core.database import mongodb
import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Sample instructor IDs (these should exist in your users collection)
INSTRUCTOR_IDS = [
    "67a1b2c3d4e5f67890123456",  # Replace with actual instructor IDs
    "67a1b2c3d4e5f67890123457",
    "67a1b2c3d4e5f67890123458"
]

COURSES_DATA = [
    {
        "title": "Introduction to Prompt Engineering",
        "slug": "intro-prompt-engineering",
        "description": "Learn the fundamentals of crafting effective prompts for AI models. Understand how to communicate with AI systems to get better results.",
        "short_description": "Master the art of communicating with AI models",
        "difficulty": "beginner",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[0],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&auto=format&fit=crop",
        "total_lessons": 12,
        "total_duration": 6.5,
        "enrolled_count": 1245,
        "review_count": 89,
        "average_rating": 4.7,
        "tags": ["ai", "prompting", "beginner", "llm"],
        "learning_outcomes": [
            "Understand prompt engineering fundamentals",
            "Write effective prompts for various tasks",
            "Debug and improve prompt performance",
            "Use advanced prompting techniques"
        ],
        "prerequisites": ["Basic computer skills"],
        "xp_reward": 1000,
        "price": 0,
        "created_at": datetime(2024, 1, 15),
        "updated_at": datetime(2024, 3, 1),
        "lesson_order": [
            "lesson_1_intro",
            "lesson_2_basics",
            "lesson_3_techniques",
            "lesson_4_advanced",
            "lesson_5_practice"
        ]
    },
    {
        "title": "Advanced LLM Fine-tuning",
        "slug": "advanced-llm-fine-tuning",
        "description": "Dive deep into fine-tuning large language models for specific tasks and domains. Learn parameter-efficient fine-tuning techniques.",
        "short_description": "Master fine-tuning techniques for specialized AI models",
        "difficulty": "advanced",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[1],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&auto=format&fit=crop",
        "total_lessons": 18,
        "total_duration": 12.0,
        "enrolled_count": 843,
        "review_count": 67,
        "average_rating": 4.8,
        "tags": ["ai", "llm", "fine-tuning", "advanced", "machine-learning"],
        "learning_outcomes": [
            "Understand LLM architecture and training",
            "Implement parameter-efficient fine-tuning",
            "Create domain-specific models",
            "Optimize model performance"
        ],
        "prerequisites": ["Python", "Machine Learning basics", "PyTorch"],
        "xp_reward": 2500,
        "price": 49.99,
        "created_at": datetime(2024, 2, 10),
        "updated_at": datetime(2024, 3, 15),
        "lesson_order": []
    },
    {
        "title": "RAG Systems Implementation",
        "slug": "rag-systems-implementation",
        "description": "Build Retrieval-Augmented Generation systems from scratch. Learn to combine search with generation for accurate AI responses.",
        "short_description": "Build AI systems that combine retrieval and generation",
        "difficulty": "intermediate",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[0],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1629654291660-3c98113a0438?w=800&auto=format&fit=crop",
        "total_lessons": 15,
        "total_duration": 10.0,
        "enrolled_count": 1567,
        "review_count": 124,
        "average_rating": 4.6,
        "tags": ["rag", "retrieval", "generation", "ai-systems", "intermediate"],
        "learning_outcomes": [
            "Design RAG system architecture",
            "Implement vector databases",
            "Build retrieval pipelines",
            "Optimize generation quality"
        ],
        "prerequisites": ["Python", "Basic AI knowledge"],
        "xp_reward": 2000,
        "price": 29.99,
        "created_at": datetime(2024, 1, 25),
        "updated_at": datetime(2024, 3, 10),
        "lesson_order": []
    },
    {
        "title": "AI Agents and Autonomous Systems",
        "slug": "ai-agents-autonomous-systems",
        "description": "Learn to build autonomous AI agents that can reason, plan, and execute tasks independently.",
        "short_description": "Create autonomous AI agents for complex tasks",
        "difficulty": "advanced",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[2],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1677742580018-b3b7cd92bd18?w=800&auto=format&fit=crop",
        "total_lessons": 20,
        "total_duration": 15.0,
        "enrolled_count": 723,
        "review_count": 56,
        "average_rating": 4.9,
        "tags": ["ai-agents", "autonomous", "reasoning", "planning", "advanced"],
        "learning_outcomes": [
            "Design agent architectures",
            "Implement reasoning systems",
            "Build planning algorithms",
            "Create multi-agent systems"
        ],
        "prerequisites": ["Python", "AI fundamentals", "Advanced programming"],
        "xp_reward": 3000,
        "price": 79.99,
        "created_at": datetime(2024, 2, 20),
        "updated_at": datetime(2024, 3, 20),
        "lesson_order": []
    },
    {
        "title": "Prompt Evaluation and Optimization",
        "slug": "prompt-evaluation-optimization",
        "description": "Learn systematic approaches to evaluate and optimize prompts using metrics, testing frameworks, and optimization techniques.",
        "short_description": "Systematically evaluate and optimize AI prompts",
        "difficulty": "intermediate",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[1],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&auto=format&fit=crop",
        "total_lessons": 14,
        "total_duration": 8.5,
        "enrolled_count": 1892,
        "review_count": 145,
        "average_rating": 4.7,
        "tags": ["evaluation", "optimization", "metrics", "testing", "intermediate"],
        "learning_outcomes": [
            "Design evaluation metrics",
            "Build testing frameworks",
            "Implement optimization algorithms",
            "Create A/B testing systems"
        ],
        "prerequisites": ["Basic prompt engineering", "Python"],
        "xp_reward": 1800,
        "price": 39.99,
        "created_at": datetime(2024, 1, 30),
        "updated_at": datetime(2024, 3, 5),
        "lesson_order": []
    },
    {
        "title": "Multimodal AI Systems",
        "slug": "multimodal-ai-systems",
        "description": "Build AI systems that can process and understand multiple modalities - text, images, audio, and video.",
        "short_description": "Create AI systems that understand multiple data types",
        "difficulty": "advanced",
        "status": "published",
        "category": "ai",
        "instructor_id": INSTRUCTOR_IDS[2],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800&auto=format&fit=crop",
        "total_lessons": 16,
        "total_duration": 11.0,
        "enrolled_count": 645,
        "review_count": 42,
        "average_rating": 4.8,
        "tags": ["multimodal", "vision", "audio", "video", "advanced"],
        "learning_outcomes": [
            "Process multiple data modalities",
            "Fuse information from different sources",
            "Build cross-modal understanding",
            "Optimize multimodal systems"
        ],
        "prerequisites": ["Deep Learning", "Python", "Computer Vision basics"],
        "xp_reward": 2200,
        "price": 59.99,
        "created_at": datetime(2024, 2, 5),
        "updated_at": datetime(2024, 3, 12),
        "lesson_order": []
    },
    {
        "title": "Ethical AI and Prompt Safety",
        "slug": "ethical-ai-prompt-safety",
        "description": "Learn about ethical considerations, bias mitigation, and safety measures in AI systems and prompt engineering.",
        "short_description": "Ensure your AI systems are ethical and safe",
        "difficulty": "intermediate",
        "status": "published",
        "category": "ethics",
        "instructor_id": INSTRUCTOR_IDS[0],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop",
        "total_lessons": 10,
        "total_duration": 6.0,
        "enrolled_count": 2310,
        "review_count": 178,
        "average_rating": 4.9,
        "tags": ["ethics", "safety", "bias", "fairness", "intermediate"],
        "learning_outcomes": [
            "Identify ethical issues in AI",
            "Mitigate bias in models",
            "Implement safety measures",
            "Design ethical guidelines"
        ],
        "prerequisites": ["Basic AI knowledge"],
        "xp_reward": 1200,
        "price": 0,
        "created_at": datetime(2024, 1, 20),
        "updated_at": datetime(2024, 3, 3),
        "lesson_order": []
    },
    {
        "title": "Vector Databases for AI",
        "slug": "vector-databases-for-ai",
        "description": "Master vector databases like Pinecone, Weaviate, and ChromaDB for efficient similarity search in AI applications.",
        "short_description": "Build efficient similarity search systems",
        "difficulty": "intermediate",
        "status": "published",
        "category": "databases",
        "instructor_id": INSTRUCTOR_IDS[1],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
        "total_lessons": 12,
        "total_duration": 7.5,
        "enrolled_count": 1423,
        "review_count": 96,
        "average_rating": 4.6,
        "tags": ["vector-db", "similarity-search", "embeddings", "databases", "intermediate"],
        "learning_outcomes": [
            "Design vector database schemas",
            "Implement similarity search",
            "Optimize query performance",
            "Scale vector databases"
        ],
        "prerequisites": ["Python", "Basic database knowledge"],
        "xp_reward": 1500,
        "price": 34.99,
        "created_at": datetime(2024, 2, 15),
        "updated_at": datetime(2024, 3, 18),
        "lesson_order": []
    },
    {
        "title": "AI-Powered Chatbot Development",
        "slug": "ai-chatbot-development",
        "description": "Build intelligent chatbots using modern AI frameworks. Learn conversation design, context management, and deployment.",
        "short_description": "Create intelligent AI chatbots",
        "difficulty": "beginner",
        "status": "published",
        "category": "applications",
        "instructor_id": INSTRUCTOR_IDS[0],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=800&auto=format&fit=crop",
        "total_lessons": 10,
        "total_duration": 5.5,
        "enrolled_count": 3124,
        "review_count": 234,
        "average_rating": 4.5,
        "tags": ["chatbots", "conversation", "nlp", "beginner", "applications"],
        "learning_outcomes": [
            "Design chatbot conversations",
            "Implement context management",
            "Deploy chatbot applications",
            "Monitor and improve chatbot performance"
        ],
        "prerequisites": ["Basic programming"],
        "xp_reward": 800,
        "price": 19.99,
        "created_at": datetime(2024, 1, 10),
        "updated_at": datetime(2024, 2, 28),
        "lesson_order": []
    },
    {
        "title": "AI Model Deployment and Scaling",
        "slug": "ai-model-deployment-scaling",
        "description": "Learn to deploy AI models to production and scale them efficiently. Cover containerization, APIs, monitoring, and optimization.",
        "short_description": "Deploy and scale AI models in production",
        "difficulty": "intermediate",
        "status": "published",
        "category": "devops",
        "instructor_id": INSTRUCTOR_IDS[2],
        "language": "english",
        "thumbnail_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
        "total_lessons": 13,
        "total_duration": 9.0,
        "enrolled_count": 987,
        "review_count": 78,
        "average_rating": 4.7,
        "tags": ["deployment", "scaling", "devops", "production", "intermediate"],
        "learning_outcomes": [
            "Containerize AI models",
            "Build scalable APIs",
            "Implement monitoring systems",
            "Optimize model serving"
        ],
        "prerequisites": ["Python", "Docker basics", "Cloud basics"],
        "xp_reward": 1700,
        "price": 44.99,
        "created_at": datetime(2024, 2, 25),
        "updated_at": datetime(2024, 3, 22),
        "lesson_order": []
    }
]


async def seed_courses():
    """Seed courses into MongoDB"""
    try:
        # Connect to MongoDB
        await mongodb.connect()

        # Get courses collection
        courses_collection = mongodb.db.courses

        # Clear existing courses (optional)
        await courses_collection.delete_many({})
        print("Cleared existing courses")

        # Insert new courses
        result = await courses_collection.insert_many(COURSES_DATA)

        print(f"Successfully seeded {len(result.inserted_ids)} courses")
        print("Course IDs:")
        for i, course_id in enumerate(result.inserted_ids, 1):
            course = COURSES_DATA[i-1]
            print(f"  {i}. {course['title']} -> {course_id}")

    except Exception as e:
        print(f"Error seeding courses: {e}")
    finally:
        await mongodb.disconnect()


async def seed_instructors():
    """Create sample instructors if they don't exist"""
    try:
        await mongodb.connect()
        users_collection = mongodb.db.users

        instructors = [
            {
                "email": "instructor1@example.com",
                "full_name": "Dr. Alex Johnson",
                "role": "instructor",
                "bio": "AI researcher with 10+ years of experience in NLP and prompt engineering",
                "avatar_url": "https://randomuser.me/api/portraits/men/32.jpg"
            },
            {
                "email": "instructor2@example.com",
                "full_name": "Sarah Chen",
                "role": "instructor",
                "bio": "ML engineer specializing in fine-tuning and model optimization",
                "avatar_url": "https://randomuser.me/api/portraits/women/44.jpg"
            },
            {
                "email": "instructor3@example.com",
                "full_name": "Marcus Rodriguez",
                "role": "instructor",
                "bio": "AI systems architect focused on scalable and ethical AI implementations",
                "avatar_url": "https://randomuser.me/api/portraits/men/67.jpg"
            }
        ]

        for instructor in instructors:
            # Check if instructor exists
            existing = await users_collection.find_one({"email": instructor["email"]})
            if not existing:
                result = await users_collection.insert_one({
                    **instructor,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_active": True
                })
                print(
                    f"Created instructor: {instructor['full_name']} ({result.inserted_id})")
            else:
                print(f"Instructor already exists: {instructor['full_name']}")

    except Exception as e:
        print(f"Error seeding instructors: {e}")
    finally:
        await mongodb.disconnect()


async def main():
    """Main seeding function"""
    print("Starting database seeding...")

    # First, create instructors
    print("\n1. Seeding instructors...")
    await seed_instructors()

    # Then, create courses
    print("\n2. Seeding courses...")
    await seed_courses()

    print("\nSeeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

"""Seed the "Prompt Engineering Academy" course documents.

The frontend calls GET /api/v1/courses/academy which expects 3 documents in the
MongoDB `courses` collection with ids:
- basics
- rag
- advanced

This script upserts those documents (so it's safe to re-run).

Run:
  python seed_academy_courses.py
"""

import asyncio
from datetime import datetime

from core.database import mongodb


ACADEMY_COURSES = [
    {
        "id": "basics",
        "title": "Prompt Engineering Basics",
        "subtitle": "Foundations for effective prompting and iteration",
        "difficulty": "beginner",
        "estimatedHours": 6,
        "audience": "Beginners who want a practical introduction to prompting",
        "badge": "Foundations",
        "primaryColor": "#4F46E5",
        "keyTopics": [
            "Prompt anatomy",
            "Clarity & constraints",
            "Examples",
            "Iteration",
        ],
        "outcomes": [
            "Write clear prompts with constraints and expected output format.",
            "Iterate on prompts using a simple evaluation loop.",
            "Use examples to reduce ambiguity and improve reliability.",
        ],
        "modules": [
            {
                "id": "basics-foundations",
                "title": "Foundations: how LLMs respond to prompts",
                "summary": "A mental model for why prompts matter and how models interpret them.",
                "lessonMarkdown": "# Foundations\n\nLarge language models predict the next token. Your prompt shapes the probability space.\n\n## Key takeaway\nBe explicit about goals, constraints, and output format.",
                "duration": "15m",
                "focus": "mental-model",
                "points": 50,
                "question": {
                    "id": "basics-foundations-q",
                    "prompt": "What is the primary goal of prompt engineering when using LLMs?",
                    "options": [
                        "Modify the model weights",
                        "Design clear instructions/context so outputs are reliable",
                        "Reduce model size",
                        "Replace the training data",
                    ],
                    "correctIndex": 1,
                    "explanation": "Prompt engineering is about communicating effectively with the model via instructions, context, and examples.",
                },
            },
            {
                "id": "basics-anatomy",
                "title": "Prompt anatomy and structure",
                "summary": "Instructions, context, inputs, and output formatting.",
                "lessonMarkdown": "# Prompt anatomy\n\nA strong prompt usually includes:\n- Role (optional)\n- Goal\n- Context\n- Constraints\n- Output format\n- Examples\n",
                "duration": "20m",
                "focus": "structure",
                "points": 75,
                "question": {
                    "id": "basics-anatomy-q",
                    "prompt": "Which is NOT a core building block of a well-structured prompt?",
                    "options": [
                        "Clear instructions",
                        "Relevant context",
                        "Input data/question",
                        "GPU type used to host the model",
                    ],
                    "correctIndex": 3,
                    "explanation": "Hardware details are generally irrelevant to prompt structure.",
                },
            },
            {
                "id": "basics-iteration",
                "title": "Iterative refinement loop",
                "summary": "Try → observe → tweak patterns for improving prompts.",
                "lessonMarkdown": "# Iteration\n\nWorkflow:\n1. Draft prompt\n2. Test on representative inputs\n3. Identify failure modes\n4. Add constraints/examples\n5. Repeat\n",
                "duration": "20m",
                "focus": "iteration",
                "points": 75,
                "question": {
                    "id": "basics-iteration-q",
                    "prompt": "Why is an iterative loop important in prompt engineering?",
                    "options": [
                        "Prompts always work on the first try",
                        "You can refine prompts based on observed failures",
                        "LLMs can only be queried a fixed number of times",
                        "It guarantees 100% accuracy",
                    ],
                    "correctIndex": 1,
                    "explanation": "Iteration helps you learn from the model's behavior and refine prompts step by step.",
                },
            },
        ],
    },
    {
        "id": "rag",
        "title": "Prompt Engineering for RAG",
        "subtitle": "Grounded answers with retrieval and citations",
        "difficulty": "intermediate",
        "estimatedHours": 8,
        "audience": "Builders integrating LLMs with external knowledge",
        "badge": "RAG",
        "primaryColor": "#0EA5E9",
        "keyTopics": [
            "Retrieval pipeline",
            "Grounding",
            "Citation prompts",
            "Refusal patterns",
        ],
        "outcomes": [
            "Write prompts that force answers to use provided context.",
            "Design refusal behavior when context is insufficient.",
            "Request citations/attribution in outputs.",
        ],
        "modules": [
            {
                "id": "rag-architecture",
                "title": "RAG architecture overview",
                "summary": "How indexing, retrieval, and generation work together.",
                "lessonMarkdown": "# RAG architecture\n\nRAG = Retrieval + Generation. Retrieval selects relevant chunks; generation composes the answer using those chunks.",
                "duration": "20m",
                "focus": "architecture",
                "points": 80,
                "question": {
                    "id": "rag-architecture-q",
                    "prompt": "In a RAG system, what does retrieval do?",
                    "options": [
                        "Trains the base model",
                        "Brings relevant external documents to ground the answer",
                        "Compresses model parameters",
                        "Replaces the language model",
                    ],
                    "correctIndex": 1,
                    "explanation": "Retrieval fetches relevant context so the model can answer grounded in evidence.",
                },
            },
            {
                "id": "rag-grounding",
                "title": "Grounding prompts with citations",
                "summary": "Force use of context and request citations.",
                "lessonMarkdown": "# Grounding\n\nPattern: \"Answer only using the provided context. If not present, say you don't know. Include citations.\"",
                "duration": "25m",
                "focus": "prompting",
                "points": 100,
                "question": {
                    "id": "rag-grounding-q",
                    "prompt": "Which prompt best encourages grounded, citation-rich answers?",
                    "options": [
                        "Answer from general knowledge only.",
                        "Ignore the context and be creative.",
                        "Answer only using provided context; if missing say you don't know; cite sources.",
                        "Always give an answer even if context is empty.",
                    ],
                    "correctIndex": 2,
                    "explanation": "Explicitly constraining the model to use context and refuse when missing reduces hallucinations.",
                },
            },
            {
                "id": "rag-evaluation",
                "title": "Evaluating RAG prompts",
                "summary": "Common failure modes: missing context, bad retrieval, vague instructions.",
                "lessonMarkdown": "# Evaluation\n\nCheck:\n- Retrieval quality\n- Context window usage\n- Citation correctness\n- Refusal behavior\n",
                "duration": "20m",
                "focus": "evaluation",
                "points": 80,
                "question": {
                    "id": "rag-evaluation-q",
                    "prompt": "If the model hallucinates in RAG, what's the first thing to check?",
                    "options": [
                        "Whether the prompt includes refusal instructions",
                        "Whether retrieval returned relevant context",
                        "Whether the GPU is fast enough",
                        "Whether the model temperature is 0",
                    ],
                    "correctIndex": 1,
                    "explanation": "Hallucinations often occur when retrieval fails or returns irrelevant context; verify retrieval first.",
                },
            },
        ],
    },
    {
        "id": "advanced",
        "title": "Advanced Prompt Engineering",
        "subtitle": "Reasoning patterns, self-critique, and orchestration",
        "difficulty": "advanced",
        "estimatedHours": 10,
        "audience": "Practitioners building complex multi-step workflows",
        "badge": "Advanced",
        "primaryColor": "#22C55E",
        "keyTopics": [
            "Decomposition",
            "Self-critique",
            "Tool use",
            "Guardrails",
        ],
        "outcomes": [
            "Use structured decomposition for complex tasks.",
            "Apply self-critique prompts to reduce mistakes.",
            "Design prompts for tool-using workflows.",
        ],
        "modules": [
            {
                "id": "adv-decomposition",
                "title": "Decompose complex tasks",
                "summary": "Break problems into smaller steps for reliability.",
                "lessonMarkdown": "# Decomposition\n\nAsk for a plan/outline first, then fill in details. Use explicit steps and intermediate checks.",
                "duration": "25m",
                "focus": "reasoning",
                "points": 120,
                "question": {
                    "id": "adv-decomposition-q",
                    "prompt": "What is a key benefit of step-by-step reasoning prompts?",
                    "options": [
                        "They guarantee correctness",
                        "They encourage breaking the problem into smaller steps",
                        "They reduce token usage",
                        "They hide all reasoning",
                    ],
                    "correctIndex": 1,
                    "explanation": "Decomposition helps the model structure reasoning and reduces missed constraints.",
                },
            },
            {
                "id": "adv-self-critique",
                "title": "Self-critique and revision",
                "summary": "Ask the model to critique its own output and revise.",
                "lessonMarkdown": "# Self-critique\n\nPattern:\n1) Draft answer\n2) Critique for errors/omissions\n3) Produce revised answer\n",
                "duration": "25m",
                "focus": "quality",
                "points": 120,
                "question": {
                    "id": "adv-self-critique-q",
                    "prompt": "Self-correction prompts typically ask the model to do what?",
                    "options": [
                        "Randomly change its answer",
                        "Ignore previous reasoning",
                        "Critique its own answer and revise if needed",
                        "Stop generating output",
                    ],
                    "correctIndex": 2,
                    "explanation": "Self-critique patterns catch simple mistakes by forcing review and revision.",
                },
            },
            {
                "id": "adv-orchestration",
                "title": "Orchestrate multi-step workflows",
                "summary": "Use tool-calling patterns and structured outputs.",
                "lessonMarkdown": "# Orchestration\n\nDesign prompts with clear I/O contracts (JSON), tool usage rules, and validation steps.",
                "duration": "20m",
                "focus": "tools",
                "points": 100,
                "question": {
                    "id": "adv-orchestration-q",
                    "prompt": "What is a best practice when asking for structured output?",
                    "options": [
                        "Ask for free-form text only",
                        "Specify a strict schema (e.g., JSON) and validation rules",
                        "Avoid constraints",
                        "Always set temperature to 1",
                    ],
                    "correctIndex": 1,
                    "explanation": "Clear schemas and validation rules make parsing and downstream automation more reliable.",
                },
            },
        ],
    },
]


async def seed_academy_courses() -> None:
    await mongodb.connect()
    try:
        courses = mongodb.db.courses

        for course in ACADEMY_COURSES:
            now = datetime.utcnow()
            doc = {
                **course,
                "updated_at": now,
            }

            existing = await courses.find_one({"id": course["id"]}, {"_id": 1})
            if existing:
                await courses.update_one({"_id": existing["_id"]}, {"$set": doc})
            else:
                doc["created_at"] = now
                await courses.insert_one(doc)

        print(f"Upserted {len(ACADEMY_COURSES)} academy course docs into `courses` collection.")
    finally:
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_academy_courses())

# server.py - Chatbot endpoints only
from fastapi import APIRouter
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

from services.chatbot_service import ChatbotService
from utils import logger

load_dotenv()

# Initialize chatbot service
chatbot_service = None


def init_chatbot_service():
    """Initialize the chatbot service"""
    global chatbot_service
    try:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is required")

        chatbot_service = ChatbotService(gemini_api_key)

        # Ensure knowledge base has content
        async def initialize_knowledge_base():
            await chatbot_service.ensure_knowledge_base()

        # Run initialization in background
        import asyncio
        asyncio.create_task(initialize_knowledge_base())

        logger.info("Chatbot service initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize chatbot service: {e}")
        chatbot_service = None


# Initialize on import
init_chatbot_service()

# Create FastAPI router for chatbot endpoints

chatbot_router = APIRouter(prefix="/chat", tags=["chatbot"])

# -------------------------------
# Chatbot Pydantic Models
# -------------------------------


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_context: bool = True


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    context_used: bool
    suggestions: List[str] = []
    sources: List[dict] = []
    processing_time_ms: float


class Conversation(BaseModel):
    id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None

# -------------------------------
# Chatbot Endpoints
# -------------------------------


@chatbot_router.post("/ask", response_model=ChatResponse)
async def chat_ask(request: ChatRequest):
    """
    Send a message to the chatbot and get a response.

    If conversation_id is provided, continue that conversation.
    Otherwise, start a new conversation.
    """
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    try:
        result = await chatbot_service.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            include_context=request.include_context
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@chatbot_router.get("/conversations", response_model=List[Conversation])
async def list_conversations(limit: int = 20):
    """List all conversations"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    try:
        conversations = chatbot_service.list_conversations(limit)
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chatbot_router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    conversation = chatbot_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@chatbot_router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    success = chatbot_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "deleted", "conversation_id": conversation_id}


@chatbot_router.delete("/conversations")
async def clear_all_conversations():
    """Clear all conversations"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    count = chatbot_service.clear_conversations()
    return {"status": "cleared", "count": count}


@chatbot_router.post("/knowledge-base/refresh")
async def refresh_knowledge_base():
    """Refresh the chatbot's knowledge base with latest content"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    try:
        result = await chatbot_service.refresh_knowledge_base()
        return result
    except Exception as e:
        logger.error(f"Failed to refresh knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chatbot_router.get("/knowledge-base/stats")
async def knowledge_base_stats():
    """Get knowledge base statistics"""
    if not chatbot_service:
        raise HTTPException(
            status_code=503, detail="Chatbot service is not available")

    try:
        stats = chatbot_service.get_knowledge_base_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get knowledge base stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chatbot_router.get("/health")
async def chat_health():
    """Check chatbot health"""
    if not chatbot_service:
        return {"status": "unavailable", "service": "chatbot"}

    try:
        stats = chatbot_service.get_knowledge_base_stats()
        return {
            "status": "healthy",
            "service": "chatbot",
            "knowledge_base": stats.get("status", "unknown"),
            "document_count": stats.get("document_count", 0)
        }
    except Exception as e:
        return {"status": "degraded", "service": "chatbot", "error": str(e)}

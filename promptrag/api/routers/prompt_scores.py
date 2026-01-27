# api/routers/prompt_scores.py
"""Endpoints for storing and retrieving prompt evaluation scores for users."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from core.security import get_current_active_user
from models.user import UserInDB
from schemas.response import APIResponse
from core.database import mongodb
from bson import ObjectId

router = APIRouter(prefix="/prompt-scores", tags=["prompt-scores"])


class ScoreEntry(BaseModel):
    prompt: str
    overall_score: float
    scores: dict
    trace_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@router.post("/save", response_model=APIResponse[dict])
async def save_score(
    entry: ScoreEntry,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save a prompt evaluation score for the current user"""
    try:
        if mongodb.db is None:
            await mongodb.connect()
        
        score_doc = {
            "user_id": str(current_user.id),
            "prompt": entry.prompt,
            "overall_score": entry.overall_score,
            "scores": entry.scores,
            "trace_id": entry.trace_id,
            "timestamp": entry.timestamp or datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }

        result = await mongodb.db.prompt_scores.insert_one(score_doc)
        
        return APIResponse(
            success=True,
            data={"score_id": str(result.inserted_id)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving score: {str(e)}",
        )


@router.get("/history", response_model=APIResponse[List[dict]])
async def get_score_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get score history for the current user"""
    try:
        if mongodb.db is None:
            await mongodb.connect()
        
        cursor = mongodb.db.prompt_scores.find(
            {"user_id": str(current_user.id)}
        ).sort("timestamp", -1).limit(limit)

        scores = await cursor.to_list(length=limit)
        
        result = []
        for score in scores:
            timestamp = score.get("timestamp") or score.get("created_at")
            result.append({
                "id": str(score["_id"]),
                "prompt": score.get("prompt", ""),
                "overall_score": score.get("overall_score", 0),
                "scores": score.get("scores", {}),
                "timestamp": timestamp.isoformat() if timestamp else None,
            })

        return APIResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting score history: {str(e)}",
        )


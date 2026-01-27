# api/routers/templates.py
"""Template management endpoints for admins."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from core.security import get_current_active_user, require_role
from models.user import UserInDB, UserRole
from schemas.response import APIResponse
from core.database import mongodb
from bson import ObjectId

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    title: str
    description: Optional[str] = None
    domain: str
    category: str
    difficulty: str
    prompt: str
    tags: Optional[List[str]] = None
    include_eval: bool = True


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    prompt: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@router.post("/create", response_model=APIResponse[dict])
async def create_template(
    template: TemplateCreate,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Create a new prompt template (admin only)"""
    try:
        if mongodb.db is None:
            await mongodb.connect()

        # Validate required fields
        if not template.title or not template.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title is required",
            )

        if not template.prompt or not template.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt is required",
            )

        if len(template.prompt.strip()) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt must be at least 20 characters",
            )

        if not template.domain or not template.category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain and category are required",
            )

        template_doc = {
            "title": template.title,
            "description": template.description or "",
            "domain": template.domain,
            "category": template.category,
            "difficulty": template.difficulty,
            "content": template.prompt,
            "tags": template.tags or [],
            "status": "active",
            "createdBy": str(current_user.id),
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "stats": {
                "uses": 0,
                "avgScore": 0.0,
            },
        }

        result = await mongodb.db.templates.insert_one(template_doc)

        return APIResponse(
            success=True,
            data={"template_id": str(result.inserted_id),
                  "message": "Template created successfully"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}",
        )


@router.get("/list", response_model=APIResponse[List[dict]])
async def list_templates(
    domain: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: Optional[UserInDB] = Depends(get_current_active_user)
):
    """Get list of templates (public, but admin can see all statuses)"""
    try:
        if mongodb.db is None:
            await mongodb.connect()

        query = {}
        if domain:
            query["domain"] = domain
        if category:
            query["category"] = category
        if difficulty:
            query["difficulty"] = difficulty

        # Non-admins can only see active templates
        if not current_user or current_user.role != UserRole.ADMIN:
            query["status"] = "active"
        elif status_filter:
            query["status"] = status_filter

        cursor = mongodb.db.templates.find(query).sort(
            "createdAt", -1).skip(skip).limit(limit)
        templates = await cursor.to_list(length=limit)

        result = []
        for template in templates:
            result.append({
                "_id": str(template["_id"]),
                "title": template.get("title", ""),
                "description": template.get("description", ""),
                "domain": template.get("domain", ""),
                "category": template.get("category", ""),
                "difficulty": template.get("difficulty", ""),
                "content": template.get("content", ""),
                "tags": template.get("tags", []),
                "status": template.get("status", "active"),
                "createdBy": template.get("createdBy", ""),
                "createdAt": template.get("createdAt", datetime.utcnow()).isoformat(),
                "updatedAt": template.get("updatedAt", datetime.utcnow()).isoformat(),
                "stats": template.get("stats", {"uses": 0, "avgScore": 0.0}),
            })

        return APIResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting templates: {str(e)}",
        )


@router.put("/{template_id}", response_model=APIResponse[dict])
async def update_template(
    template_id: str,
    template: TemplateUpdate,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Update a template (admin only)"""
    try:
        if mongodb.db is None:
            await mongodb.connect()

        update_dict = {k: v for k, v in template.dict(
            exclude_unset=True).items() if v is not None}

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        update_dict["updatedAt"] = datetime.utcnow()

        result = await mongodb.db.templates.update_one(
            {"_id": ObjectId(template_id)},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )

        return APIResponse(
            success=True,
            data={"message": "Template updated successfully"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}",
        )


@router.delete("/{template_id}", response_model=APIResponse[dict])
async def delete_template(
    template_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Delete a template (admin only)"""
    try:
        if mongodb.db is None:
            await mongodb.connect()

        result = await mongodb.db.templates.delete_one({"_id": ObjectId(template_id)})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )

        return APIResponse(
            success=True,
            data={"message": "Template deleted successfully"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting template: {str(e)}",
        )

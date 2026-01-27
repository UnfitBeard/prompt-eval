# api/routers/admin.py
"""Admin dashboard and management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from core.security import get_current_active_user, require_role
from models.user import UserInDB, UserRole
from schemas.response import APIResponse
from services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])
admin_service = AdminService()


@router.get("/dashboard/stats", response_model=APIResponse[dict])
async def get_dashboard_stats(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get comprehensive dashboard statistics (admin only)"""
    try:
        stats = await admin_service.get_dashboard_stats()
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard stats: {str(e)}",
        )


@router.get("/traces", response_model=APIResponse[dict])
async def get_evaluation_traces(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    trace_id: Optional[str] = None,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get evaluation traces (admin only)"""
    try:
        result = await admin_service.get_evaluation_traces(limit, offset, trace_id)
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching traces: {str(e)}",
        )


@router.delete("/traces/{trace_id}", response_model=APIResponse[dict])
async def delete_evaluation_trace(
    trace_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Delete an evaluation trace (admin only)"""
    try:
        deleted = await admin_service.delete_evaluation_trace(trace_id)
        if deleted:
            return APIResponse(success=True, data={"message": "Trace deleted successfully"})
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting trace: {str(e)}",
        )


@router.get("/system/performance", response_model=APIResponse[dict])
async def get_system_performance(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get system performance metrics (admin only)"""
    try:
        performance = admin_service.get_system_performance()
        return APIResponse(success=True, data=performance)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching system performance: {str(e)}",
        )


@router.get("/models/config", response_model=APIResponse[dict])
async def get_model_configurations(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get current model configurations (admin only)"""
    try:
        config = admin_service.get_model_configurations()
        return APIResponse(success=True, data=config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching model configurations: {str(e)}",
        )


class ModelConfigUpdate(BaseModel):
    embedder_name: Optional[str] = None
    version: Optional[str] = None
    # Add other configurable parameters as needed


@router.put("/models/config", response_model=APIResponse[dict])
async def update_model_configuration(
    config: ModelConfigUpdate,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Update model configuration (admin only)"""
    # For now, this is a placeholder - actual model updates would require
    # retraining or reloading models
    try:
        # TODO: Implement actual model configuration update logic
        return APIResponse(
            success=True,
            data={"message": "Model configuration update not yet implemented"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating model configuration: {str(e)}",
        )


@router.get("/system/usage", response_model=APIResponse[dict])
async def get_system_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get system usage statistics (admin only)"""
    try:
        # Get usage stats from evaluation history
        from datetime import datetime, timedelta
        import sqlite3

        start_date = datetime.utcnow() - timedelta(days=days)

        conn = sqlite3.connect('prompt_history.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Daily usage
        c.execute(
            """SELECT DATE(timestamp) as date, COUNT(*) as count
               FROM prompt_evaluations
               WHERE timestamp >= ?
               GROUP BY DATE(timestamp)
               ORDER BY date""",
            (start_date.isoformat(),)
        )

        daily_usage = []
        for row in c.fetchall():
            daily_usage.append({
                "date": row["date"],
                "count": row["count"],
            })

        # Total usage
        c.execute(
            "SELECT COUNT(*) as count FROM prompt_evaluations WHERE timestamp >= ?",
            (start_date.isoformat(),)
        )
        total = c.fetchone()["count"]

        conn.close()

        return APIResponse(success=True, data={
            "period_days": days,
            "total_evaluations": total,
            "daily_usage": daily_usage,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching system usage: {str(e)}",
        )


@router.get("/system/maintenance", response_model=APIResponse[dict])
async def get_maintenance_info(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Get system maintenance information (admin only)"""
    try:
        # Get system info
        import platform
        import sys
        from pathlib import Path

        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "uptime": "N/A",  # TODO: Track actual uptime
            "last_update": "N/A",  # TODO: Track last update time
            "database_size_mb": 0,  # TODO: Calculate actual DB size
            "log_files": [],
        }

        # Get log files
        log_dir = Path("./logs")
        if log_dir.exists():
            log_files = [f.name for f in log_dir.glob("*.log")]
            system_info["log_files"] = log_files

        return APIResponse(success=True, data=system_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching maintenance info: {str(e)}",
        )


class CleanupRequest(BaseModel):
    days_to_keep: int = Field(90, ge=1, le=365)


@router.post("/system/maintenance/cleanup", response_model=APIResponse[dict])
async def cleanup_old_data(
    request: CleanupRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN.value))
):
    """Cleanup old evaluation data (admin only)"""
    try:
        from datetime import datetime, timedelta
        import sqlite3

        cutoff_date = datetime.utcnow() - timedelta(days=request.days_to_keep)

        conn = sqlite3.connect('prompt_history.db')
        c = conn.cursor()

        c.execute(
            "DELETE FROM prompt_evaluations WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        )

        deleted_count = c.rowcount
        conn.commit()
        conn.close()

        return APIResponse(
            success=True,
            data={
                "message": f"Cleaned up {deleted_count} old evaluation records",
                "deleted_count": deleted_count,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}",
        )


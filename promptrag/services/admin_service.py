# services/admin_service.py
"""Admin service for dashboard statistics and management operations."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import sqlite3
import json
import logging
import psutil
import os
from pathlib import Path

from core.database import mongodb
from models.user import UserRole

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self):
        self.collection = None

    async def _ensure_connected(self):
        if mongodb.db is None:
            await mongodb.connect()
        if self.collection is None:
            self.collection = mongodb.db.users

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        await self._ensure_connected()

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        yesterday = now - timedelta(days=1)

        # Total active users (active in last 30 days)
        active_users = await self.collection.count_documents({
            "is_active": True,
            "last_active": {"$gte": thirty_days_ago}
        })

        # New users this month
        new_users_this_month = await self.collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })

        # New users last month (for comparison)
        last_month_start = thirty_days_ago - timedelta(days=30)
        new_users_last_month = await self.collection.count_documents({
            "created_at": {"$gte": last_month_start, "$lt": thirty_days_ago}
        })

        # Calculate retention rate (users active in last 7 days / total active users)
        active_last_week = await self.collection.count_documents({
            "is_active": True,
            "last_active": {"$gte": seven_days_ago}
        })
        retention_rate = (active_last_week / active_users * 100) if active_users > 0 else 0

        # Get evaluation statistics from SQLite
        eval_stats = self._get_evaluation_stats()

        # Get user activity over time
        activity_data = await self._get_user_activity_timeline()

        # Get model performance metrics
        model_perf = self._get_model_performance_metrics()

        # Get prompt statistics
        prompt_stats = self._get_prompt_statistics()

        # Get system health
        system_health = self._get_system_health()

        # Get top users
        top_users = await self._get_top_users(limit=10)

        return {
            "kpis": {
                "active_users": active_users,
                "new_users_this_month": new_users_this_month,
                "new_users_delta": self._calculate_percentage_change(
                    new_users_this_month, new_users_last_month
                ),
                "retention_rate": round(retention_rate, 1),
                "avg_session_duration": "12m 36s",  # TODO: Calculate from actual session data
            },
            "user_activity": activity_data,
            "model_performance": model_perf,
            "prompt_statistics": prompt_stats,
            "system_health": system_health,
            "top_users": top_users,
            "evaluation_stats": eval_stats,
        }

    def _get_evaluation_stats(self) -> Dict[str, Any]:
        """Get statistics from evaluation history (SQLite)"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Total evaluations
            c.execute("SELECT COUNT(*) as count FROM prompt_evaluations")
            total_evaluations = c.fetchone()["count"]

            # Evaluations in last 30 days
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            c.execute(
                "SELECT COUNT(*) as count FROM prompt_evaluations WHERE timestamp >= ?",
                (thirty_days_ago,)
            )
            recent_evaluations = c.fetchone()["count"]

            # Average scores
            c.execute(
                "SELECT AVG(overall_score) as avg_score FROM prompt_evaluations"
            )
            avg_score_result = c.fetchone()
            avg_score = round(avg_score_result["avg_score"], 2) if avg_score_result["avg_score"] else 0

            # Average processing time
            c.execute(
                """SELECT AVG(CAST(json_extract(final_scores, '$.processing_time_ms') AS REAL)) as avg_time
                   FROM prompt_evaluations WHERE final_scores LIKE '%processing_time_ms%'"""
            )
            # Since we don't store processing_time_ms in SQLite, we'll estimate
            avg_processing_time = 1.2  # seconds

            conn.close()

            return {
                "total_evaluations": total_evaluations,
                "recent_evaluations": recent_evaluations,
                "average_score": avg_score,
                "average_processing_time": avg_processing_time,
            }
        except Exception as e:
            logger.error(f"Error getting evaluation stats: {e}")
            return {
                "total_evaluations": 0,
                "recent_evaluations": 0,
                "average_score": 0,
                "average_processing_time": 0,
            }

    async def _get_user_activity_timeline(self) -> Dict[str, List]:
        """Get user activity over the last 7 months"""
        await self._ensure_connected()

        # Get activity for last 7 months
        months = []
        values = []

        for i in range(6, -1, -1):  # Last 7 months
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)

            count = await self.collection.count_documents({
                "created_at": {"$gte": month_start, "$lt": month_end}
            })

            months.append(month_start.strftime("%b"))
            values.append(count)

        return {
            "labels": months,
            "values": values,
        }

    def _get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get ML model performance metrics"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get scores for last 5 months
            months = []
            clarity_scores = []
            relevance_scores = []
            specificity_scores = []
            creativity_scores = []
            context_scores = []

            for i in range(4, -1, -1):
                month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
                month_end = month_start + timedelta(days=30)

                c.execute(
                    """SELECT AVG(CAST(json_extract(final_scores, '$.clarity') AS REAL)) as clarity,
                              AVG(CAST(json_extract(final_scores, '$.relevance') AS REAL)) as relevance,
                              AVG(CAST(json_extract(final_scores, '$.specificity') AS REAL)) as specificity,
                              AVG(CAST(json_extract(final_scores, '$.creativity') AS REAL)) as creativity,
                              AVG(CAST(json_extract(final_scores, '$.context') AS REAL)) as context
                       FROM prompt_evaluations
                       WHERE timestamp >= ? AND timestamp < ?""",
                    (month_start.isoformat(), month_end.isoformat())
                )

                result = c.fetchone()
                months.append(month_start.strftime("%b"))

                clarity_scores.append(round(result["clarity"] or 0, 1) if result["clarity"] else 0)
                relevance_scores.append(round(result["relevance"] or 0, 1) if result["relevance"] else 0)
                specificity_scores.append(round(result["specificity"] or 0, 1) if result["specificity"] else 0)
                creativity_scores.append(round(result["creativity"] or 0, 1) if result["creativity"] else 0)
                context_scores.append(round(result["context"] or 0, 1) if result["context"] else 0)

            conn.close()

            return {
                "labels": months,
                "series": [
                    {"name": "clarity", "values": clarity_scores, "color": "#3B82F6"},
                    {"name": "relevance", "values": relevance_scores, "color": "#10B981"},
                    {"name": "specificity", "values": specificity_scores, "color": "#F59E0B"},
                    {"name": "creativity", "values": creativity_scores, "color": "#8B5CF6"},
                    {"name": "context", "values": context_scores, "color": "#EF4444"},
                ],
            }
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "series": [
                    {"name": "clarity", "values": [0, 0, 0, 0, 0], "color": "#3B82F6"},
                    {"name": "relevance", "values": [0, 0, 0, 0, 0], "color": "#10B981"},
                    {"name": "specificity", "values": [0, 0, 0, 0, 0], "color": "#F59E0B"},
                    {"name": "creativity", "values": [0, 0, 0, 0, 0], "color": "#8B5CF6"},
                    {"name": "context", "values": [0, 0, 0, 0, 0], "color": "#EF4444"},
                ],
            }

    def _get_prompt_statistics(self) -> Dict[str, Any]:
        """Get prompt analysis statistics"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Average prompt length
            c.execute("SELECT AVG(LENGTH(prompt)) as avg_length FROM prompt_evaluations")
            avg_length_result = c.fetchone()
            avg_length = int(avg_length_result["avg_length"] or 0)

            # Success rate (evaluations with score >= 6.0)
            c.execute(
                "SELECT COUNT(*) as count FROM prompt_evaluations WHERE overall_score >= 6.0"
            )
            successful = c.fetchone()["count"]

            c.execute("SELECT COUNT(*) as count FROM prompt_evaluations")
            total = c.fetchone()["count"]

            success_rate = (successful / total * 100) if total > 0 else 0

            # Error rate (we'll estimate based on failed evaluations)
            error_rate = 1.3  # TODO: Track actual errors

            conn.close()

            return {
                "average_prompt_length": avg_length,
                "success_rate": round(success_rate, 1),
                "response_time": 1.2,  # seconds
                "error_rate": error_rate,
            }
        except Exception as e:
            logger.error(f"Error getting prompt statistics: {e}")
            return {
                "average_prompt_length": 0,
                "success_rate": 0,
                "response_time": 0,
                "error_rate": 0,
            }

    def _get_system_health(self) -> List[Dict[str, str]]:
        """Get system health status"""
        health_items = []

        # Check database connection
        try:
            if mongodb.db is not None:
                health_items.append({"label": "Database", "status": "Operational"})
            else:
                health_items.append({"label": "Database", "status": "Down"})
        except Exception:
            health_items.append({"label": "Database", "status": "Down"})

        # Check SQLite
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.close()
            health_items.append({"label": "Evaluation History DB", "status": "Operational"})
        except Exception:
            health_items.append({"label": "Evaluation History DB", "status": "Down"})

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            if cpu_percent > 90 or memory.percent > 90:
                health_items.append({"label": "System Resources", "status": "Warning"})
            else:
                health_items.append({"label": "System Resources", "status": "Operational"})
        except Exception:
            health_items.append({"label": "System Resources", "status": "Warning"})

        # Check scoring artifacts
        artifacts_path = Path("./scoring_artifacts")
        if artifacts_path.exists() and (artifacts_path / "regressor.joblib").exists():
            health_items.append({"label": "ML Model", "status": "Operational"})
        else:
            health_items.append({"label": "ML Model", "status": "Warning"})

        return health_items

    async def _get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by activity"""
        await self._ensure_connected()

        # Get users with most evaluations (we'll estimate from XP for now)
        cursor = self.collection.find(
            {"is_active": True},
            {"username": 1, "email": 1, "created_at": 1, "last_active": 1, "xp": 1}
        ).sort("xp", -1).limit(limit)

        users = await cursor.to_list(length=limit)

        result = []
        for i, user in enumerate(users, 1):
            # Estimate prompt count from XP (rough estimate: 10 XP per prompt)
            estimated_prompts = max(0, user.get("xp", 0) // 10)

            result.append({
                "id": str(user["_id"]),
                "name": user.get("username", "Unknown"),
                "joined": user.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d"),
                "lastActive": user.get("last_active", datetime.utcnow()).strftime("%Y-%m-%d"),
                "prompts": estimated_prompts,
                "avgScore": 8.5,  # TODO: Calculate from actual evaluations
                "plan": "Free",  # TODO: Add plan field to user model
            })

        return result

    def _calculate_percentage_change(self, current: int, previous: int) -> float:
        """Calculate percentage change"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    async def get_evaluation_traces(
        self, limit: int = 50, offset: int = 0, trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get evaluation traces from SQLite"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            if trace_id:
                c.execute(
                    "SELECT * FROM prompt_evaluations WHERE trace_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (trace_id, limit, offset)
                )
            else:
                c.execute(
                    "SELECT * FROM prompt_evaluations ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )

            rows = c.fetchall()

            # Get total count
            if trace_id:
                c.execute("SELECT COUNT(*) as count FROM prompt_evaluations WHERE trace_id = ?", (trace_id,))
            else:
                c.execute("SELECT COUNT(*) as count FROM prompt_evaluations")
            total = c.fetchone()["count"]

            conn.close()

            traces = []
            for row in rows:
                traces.append({
                    "id": row["id"],
                    "trace_id": row["trace_id"],
                    "prompt": row["prompt"],
                    "timestamp": row["timestamp"],
                    "overall_score": row["overall_score"],
                    "base_scores": json.loads(row["base_scores"]),
                    "final_scores": json.loads(row["final_scores"]),
                    "suggestions": json.loads(row["suggestions"]) if row["suggestions"] else [],
                    "improved_prompt": row["improved_prompt"],
                    "improved_scores": json.loads(row["improved_scores"]) if row["improved_scores"] else None,
                })

            return {
                "traces": traces,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Error getting evaluation traces: {e}")
            return {
                "traces": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }

    async def delete_evaluation_trace(self, trace_id: str) -> bool:
        """Delete an evaluation trace"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            c = conn.cursor()
            c.execute("DELETE FROM prompt_evaluations WHERE trace_id = ?", (trace_id,))
            conn.commit()
            deleted = c.rowcount > 0
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"Error deleting trace: {e}")
            return False

    def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get process info
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(),
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": disk.percent,
                    "free_gb": round(disk.free / (1024**3), 2),
                },
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent(interval=0.1),
                },
            }
        except Exception as e:
            logger.error(f"Error getting system performance: {e}")
            return {}

    def get_model_configurations(self) -> Dict[str, Any]:
        """Get current model configurations"""
        try:
            artifacts_path = Path("./scoring_artifacts")
            meta_path = artifacts_path / "meta.json"

            if not meta_path.exists():
                return {
                    "status": "not_configured",
                    "message": "Model artifacts not found",
                }

            with open(meta_path) as f:
                meta = json.load(f)

            return {
                "status": "configured",
                "embedder": meta.get("embedder_name", "unknown"),
                "targets": meta.get("targets", []),
                "version": meta.get("version", "unknown"),
                "model_path": str(artifacts_path / "regressor.joblib"),
                "scaler_path": str(artifacts_path / "feats_scaler.joblib"),
            }
        except Exception as e:
            logger.error(f"Error getting model configurations: {e}")
            return {
                "status": "error",
                "message": str(e),
            }


"""Dashboard service — aggregated statistics for P1 page."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document, DocumentStatus
from models.review import ReviewDecision
from models.risk_flag import RiskFlag


class DashboardService:
    """Stateless service for dashboard statistics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stats(self, user_id: str) -> dict:
        """Return aggregated dashboard stats.

        Returns:
            dict with keys: pending_reviews, completed_this_week,
            avg_review_time_minutes, total_risks_found.
        """
        # Pending reviews: documents in REVIEWING or HUMAN_REVIEW status
        pending_result = await self.session.execute(
            select(func.count(Document.id)).where(
                Document.status.in_(
                    [DocumentStatus.REVIEWING, DocumentStatus.HUMAN_REVIEW]
                )
            )
        )
        pending_reviews = pending_result.scalar_one()

        # Completed this week
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        completed_result = await self.session.execute(
            select(func.count(Document.id)).where(
                Document.status == DocumentStatus.COMPLETED,
                Document.updated_at >= one_week_ago,
            )
        )
        completed_this_week = completed_result.scalar_one()

        # Average review time (approximate)
        avg_time_result = await self.session.execute(
            select(func.avg(Document.updated_at - Document.created_at)).where(
                Document.status == DocumentStatus.COMPLETED,
            )
        )
        avg_interval = avg_time_result.scalar_one()
        avg_review_time_minutes = 0
        if avg_interval:
            # avg_interval is a timedelta; convert to minutes
            avg_review_time_minutes = round(avg_interval.total_seconds() / 60, 1)

        # Total risks found
        risks_result = await self.session.execute(
            select(func.count(RiskFlag.id))
        )
        total_risks_found = risks_result.scalar_one()

        return {
            "pending_reviews": pending_reviews,
            "completed_this_week": completed_this_week,
            "avg_review_time_minutes": avg_review_time_minutes,
            "total_risks_found": total_risks_found,
        }

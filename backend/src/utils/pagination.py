"""Pagination helper — converts page/size params to SQLAlchemy offset/limit."""

from __future__ import annotations

from math import ceil
from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from schemas.common import PaginatedData, PaginationParams

T = TypeVar("T")


async def paginate(
    session: AsyncSession,
    stmt: Select,
    params: PaginationParams,
    *,
    count_stmt: Select | None = None,
) -> PaginatedData:
    """Execute a paginated query and return a PaginatedData wrapper.

    Args:
        session: An open AsyncSession.
        stmt: The SELECT statement for items (ORDER BY must be applied).
        params: page/size from the client.
        count_stmt: Optional separate count statement. If None, derived from stmt.

    Returns:
        PaginatedData with page, size, total, and items.
    """
    offset = (params.page - 1) * params.size

    # Count total
    if count_stmt is None:
        # Build a count from the original statement (drop ORDER BY, wrap in subquery)
        subq = stmt.order_by(None).subquery()
        count_stmt = select(func.count()).select_from(subq)

    total: int = (await session.execute(count_stmt)).scalar_one()

    # Fetch page
    page_stmt = stmt.offset(offset).limit(params.size)
    rows = (await session.execute(page_stmt)).scalars().all()

    return PaginatedData(
        page=params.page,
        size=params.size,
        total=total,
        items=list(rows),
    )

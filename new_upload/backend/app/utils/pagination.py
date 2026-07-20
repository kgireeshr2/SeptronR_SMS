from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.response import PaginationMeta


async def paginate(
    session: AsyncSession,
    query,
    count_query,
    page: int = 1,
    page_size: int = 20,
):
    """
    Generic pagination helper for SQLAlchemy async queries.

    Args:
        session: AsyncSession instance
        query: SQLAlchemy select query with ordering
        count_query: SQLAlchemy select count query
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)

    Returns:
        Tuple of (items list, PaginationMeta)
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size

    total_result = await session.execute(count_query)
    total = total_result.scalar_one_or_none() or 0

    paginated_query = query.offset(offset).limit(page_size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    meta = PaginationMeta(
        page=page, page_size=page_size, total=total, total_pages=total_pages
    )
    return items, meta

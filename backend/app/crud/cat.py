from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Cat


async def get_cat(db: AsyncSession, cat_id: str) -> Cat | None:
    result = await db.execute(
        select(Cat).where(Cat.id == cat_id, Cat.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()

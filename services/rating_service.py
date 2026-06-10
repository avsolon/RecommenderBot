from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Rating, Recommendation, User


async def rate_recommendation(session: AsyncSession, user_id: int, recommendation_id: int, score: int) -> Rating:
    if score < 1 or score > 5:
        raise ValueError("Score must be between 1 and 5")

    result = await session.execute(
        select(Rating).where(
            Rating.user_id == user_id,
            Rating.recommendation_id == recommendation_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.score = score
        rating = existing
    else:
        rating = Rating(user_id=user_id, recommendation_id=recommendation_id, score=score)
        session.add(rating)

    await session.commit()
    await session.refresh(rating)
    return rating


async def get_user_rating(session: AsyncSession, user_id: int, recommendation_id: int) -> int | None:
    result = await session.execute(
        select(Rating.score).where(
            Rating.user_id == user_id,
            Rating.recommendation_id == recommendation_id
        )
    )
    return result.scalar_one_or_none()


async def get_recommendation_rating_stats(session: AsyncSession, recommendation_id: int) -> dict:
    result = await session.execute(
        select(
            func.coalesce(func.avg(Rating.score), 0).label("avg_score"),
            func.count(Rating.id).label("count")
        ).where(Rating.recommendation_id == recommendation_id)
    )
    row = result.one()
    return {
        "avg_score": round(float(row[0] or 0), 1),
        "count": row[1]
    }


async def get_top_rated(session: AsyncSession, category: str = None, limit: int = 10):
    from services.recommendation_service import get_popular_recommendations
    return await get_popular_recommendations(session, category, limit)


async def get_user_given_ratings(session: AsyncSession, user_id: int, limit: int = 10):
    result = await session.execute(
        select(Rating)
        .where(Rating.user_id == user_id)
        .order_by(Rating.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

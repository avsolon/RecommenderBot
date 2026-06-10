import random
from sqlalchemy import select, func, desc, delete as sa_delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Recommendation, Rating


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str = None, first_name: str = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        if (username and user.username != username) or (first_name and user.first_name != first_name):
            user.username = username
            user.first_name = first_name
            await session.commit()
    return user


async def add_recommendation(session: AsyncSession, user_id: int, category: str, title: str, comment: str, is_public: bool = False) -> Recommendation:
    rec = Recommendation(user_id=user_id, category=category, title=title, comment=comment, is_public=is_public)
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec


async def get_user_recommendations(session: AsyncSession, user_id: int, limit: int = 10, offset: int = 0):
    result = await session.execute(
        select(Recommendation)
        .where(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
        .limit(limit).offset(offset)
    )
    return result.scalars().all()


async def get_recommendation_by_id(session: AsyncSession, rec_id: int):
    result = await session.execute(select(Recommendation).where(Recommendation.id == rec_id))
    return result.scalar_one_or_none()


async def update_recommendation(session: AsyncSession, rec_id: int, user_id: int, field: str, value) -> bool:
    allowed = {"category", "title", "comment", "is_public"}
    if field not in allowed:
        return False
    result = await session.execute(
        select(Recommendation).where(Recommendation.id == rec_id, Recommendation.user_id == user_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return False
    setattr(rec, field, value)
    await session.commit()
    return True


async def delete_recommendation(session: AsyncSession, rec_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Recommendation).where(Recommendation.id == rec_id, Recommendation.user_id == user_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return False
    await session.execute(sa_delete(Rating).where(Rating.recommendation_id == rec_id))
    await session.delete(rec)
    await session.commit()
    return True


async def toggle_public(session: AsyncSession, rec_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Recommendation).where(Recommendation.id == rec_id, Recommendation.user_id == user_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise ValueError("Recommendation not found or not owned by user")
    rec.is_public = not rec.is_public
    await session.commit()
    return rec.is_public


async def search_recommendations(session: AsyncSession, user_id: int = None, keyword: str = None, category: str = None, public_only: bool = False, limit: int = 10, offset: int = 0):
    query = select(Recommendation)

    conditions = []
    if public_only:
        conditions.append(Recommendation.is_public == True)
    if user_id:
        conditions.append(Recommendation.user_id == user_id)
    if category and category != "ALL":
        conditions.append(Recommendation.category == category)
    if keyword:
        keyword_filter = or_(
            Recommendation.title.ilike(f"%{keyword}%"),
            Recommendation.comment.ilike(f"%{keyword}%")
        )
        conditions.append(keyword_filter)

    if conditions:
        query = query.where(*conditions)

    query = query.order_by(Recommendation.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all()


async def get_popular_recommendations(session: AsyncSession, category: str = None, limit: int = 10):
    query = (
        select(
            Recommendation,
            func.coalesce(func.avg(Rating.score), 0).label("avg_score"),
            func.count(Rating.id).label("rating_count")
        )
        .outerjoin(Rating, Rating.recommendation_id == Recommendation.id)
        .where(Recommendation.is_public == True)
    )

    if category and category != "ALL":
        query = query.where(Recommendation.category == category)

    query = query.group_by(Recommendation.id)
    query = query.order_by(
        func.avg(Rating.score).desc().nullslast(),
        func.count(Rating.id).desc()
    ).limit(limit)

    result = await session.execute(query)
    rows = result.all()
    return [
        {
            "rec": row[0],
            "avg_score": round(float(row[1] or 0), 1),
            "rating_count": row[2]
        }
        for row in rows
    ]


async def get_random_recommendation(session: AsyncSession, user_id: int = None, category: str = None, public_only: bool = True):
    query = select(Recommendation)

    conditions = []
    if public_only:
        conditions.append(Recommendation.is_public == True)
    if user_id:
        conditions.append(Recommendation.user_id == user_id)
    if category and category != "ALL":
        conditions.append(Recommendation.category == category)

    if conditions:
        query = query.where(*conditions)

    result = await session.execute(query)
    rows = result.scalars().all()
    return random.choice(rows) if rows else None


async def get_public_recommendations(session: AsyncSession, category: str = None, limit: int = 10, offset: int = 0):
    return await search_recommendations(
        session=session, public_only=True,
        category=category, limit=limit, offset=offset
    )


async def get_statistics(session: AsyncSession, user_id: int):
    total_result = await session.execute(
        select(func.count(Recommendation.id)).where(Recommendation.user_id == user_id)
    )
    total = total_result.scalar()

    public_result = await session.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.user_id == user_id,
            Recommendation.is_public == True
        )
    )
    public_count = public_result.scalar()

    return {
        "total": total or 0,
        "public": public_count or 0,
        "private": (total or 0) - (public_count or 0)
    }

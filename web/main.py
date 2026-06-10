from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db import get_session, init_db
from models import User, Recommendation, Rating
from config import CATEGORIES

app = FastAPI(
    title="RecommenderBot API",
    description="API для просмотра публичных рекомендаций и рейтингов",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return {
        "name": "RecommenderBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/categories")
async def list_categories():
    return {"categories": CATEGORIES}


@app.get("/recommendations")
async def list_recommendations(
    category: str = Query(None, description="Фильтр по категории"),
    search: str = Query(None, description="Поиск по тексту"),
    page: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session)
):
    from services.recommendation_service import get_public_recommendations
    recs = await get_public_recommendations(session, category=category, limit=limit, offset=page * limit)

    result = []
    for rec in recs:
        author_name = rec.author.display_name if rec.author else "Unknown"
        cat_name = CATEGORIES.get(rec.category, rec.category)

        rating_result = await session.execute(
            select(
                func.coalesce(func.avg(Rating.score), 0),
                func.count(Rating.id)
            ).where(Rating.recommendation_id == rec.id)
        )
        avg_score, rating_count = rating_result.one()

        result.append({
            "id": rec.id,
            "title": rec.title,
            "comment": rec.comment,
            "category": cat_name,
            "category_key": rec.category,
            "author": author_name,
            "rating": round(float(avg_score or 0), 1),
            "rating_count": rating_count,
            "created_at": rec.created_at.isoformat() if rec.created_at else None
        })

    return {
        "items": result,
        "page": page,
        "limit": limit,
        "total": len(result)
    }


@app.get("/recommendations/top")
async def top_recommendations(
    category: str = Query(None, description="Фильтр по категории"),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session)
):
    from services.recommendation_service import get_popular_recommendations
    popular = await get_popular_recommendations(session, category=category, limit=limit)

    result = []
    for item in popular:
        rec = item["rec"]
        author_name = rec.author.display_name if rec.author else "Unknown"
        cat_name = CATEGORIES.get(rec.category, rec.category)

        result.append({
            "id": rec.id,
            "title": rec.title,
            "comment": rec.comment,
            "category": cat_name,
            "category_key": rec.category,
            "author": author_name,
            "avg_rating": item["avg_score"],
            "rating_count": item["rating_count"],
            "created_at": rec.created_at.isoformat() if rec.created_at else None
        })

    return {"items": result, "limit": limit}


@app.get("/recommendations/{rec_id}")
async def get_recommendation(
    rec_id: int,
    session: AsyncSession = Depends(get_session)
):
    from services.recommendation_service import get_recommendation_by_id
    from services.rating_service import get_recommendation_rating_stats

    rec = await get_recommendation_by_id(session, rec_id)
    if not rec or not rec.is_public:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    stats = await get_recommendation_rating_stats(session, rec_id)
    cat_name = CATEGORIES.get(rec.category, rec.category)
    author_name = rec.author.display_name if rec.author else "Unknown"

    return {
        "id": rec.id,
        "title": rec.title,
        "comment": rec.comment,
        "category": cat_name,
        "category_key": rec.category,
        "author": author_name,
        "is_public": rec.is_public,
        "rating": stats["avg_score"],
        "rating_count": stats["count"],
        "created_at": rec.created_at.isoformat() if rec.created_at else None
    }


@app.get("/users/{telegram_id}")
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=True)

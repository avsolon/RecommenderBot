"""
Tests for recommendation and rating services.
Uses SQLite in-memory (via SQLAlchemy) to avoid needing PostgreSQL.

Usage:
    pytest tests/test_services.py -v
    python -m pytest tests/test_services.py -v
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from db import Base
from models import User, Recommendation, Rating
from services.recommendation_service import (
    get_or_create_user, add_recommendation, get_user_recommendations,
    get_recommendation_by_id, update_recommendation, delete_recommendation,
    toggle_public, search_recommendations, get_popular_recommendations,
    get_random_recommendation, get_public_recommendations, get_statistics
)
from services.rating_service import (
    rate_recommendation, get_user_rating, get_recommendation_rating_stats
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_or_create_user(session):
    user = await get_or_create_user(session, 12345, "testuser", "Test")
    assert user.telegram_id == 12345
    assert user.username == "testuser"
    assert user.display_name == "Test"

    same_user = await get_or_create_user(session, 12345)
    assert same_user.id == user.id


@pytest.mark.asyncio
async def test_add_and_get_recommendations(session):
    user = await get_or_create_user(session, 111, "user1", "User 1")
    await add_recommendation(session, user.id, "films", "Inception", "Great movie", True)
    await add_recommendation(session, user.id, "books", "1984", "Classic", False)

    recs = await get_user_recommendations(session, user.id)
    assert len(recs) == 2
    assert recs[0].title == "1984"


@pytest.mark.asyncio
async def test_update_recommendation(session):
    user = await get_or_create_user(session, 222, "user2", "User 2")
    rec = await add_recommendation(session, user.id, "music", "Bohemian Rhapsody", "", True)

    success = await update_recommendation(session, rec.id, user.id, "title", "Love of My Life")
    assert success

    updated = await get_recommendation_by_id(session, rec.id)
    assert updated.title == "Love of My Life"


@pytest.mark.asyncio
async def test_delete_recommendation(session):
    user = await get_or_create_user(session, 333, "user3", "User 3")
    rec = await add_recommendation(session, user.id, "series", "Breaking Bad", "", False)

    success = await delete_recommendation(session, rec.id, user.id)
    assert success

    deleted = await get_recommendation_by_id(session, rec.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_toggle_public(session):
    user = await get_or_create_user(session, 444, "user4", "User 4")
    rec = await add_recommendation(session, user.id, "food", "Pizza", "", False)

    result = await toggle_public(session, rec.id, user.id)
    assert result is True

    result = await toggle_public(session, rec.id, user.id)
    assert result is False

    with pytest.raises(ValueError):
        await toggle_public(session, 99999, user.id)


@pytest.mark.asyncio
async def test_search_recommendations(session):
    user = await get_or_create_user(session, 555, "user5", "User 5")
    await add_recommendation(session, user.id, "films", "The Matrix", "Sci-fi classic", True)
    await add_recommendation(session, user.id, "books", "Dune", "Another sci-fi", False)

    results = await search_recommendations(session, user_id=user.id, keyword="Matrix")
    assert len(results) == 1
    assert results[0].title == "The Matrix"

    results = await search_recommendations(session, user_id=user.id, keyword="sci-fi")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_rating(session):
    user1 = await get_or_create_user(session, 101, "alice", "Alice")
    user2 = await get_or_create_user(session, 102, "bob", "Bob")
    rec = await add_recommendation(session, user1.id, "films", "Interstellar", "Amazing", True)

    rating = await rate_recommendation(session, user2.id, rec.id, 5)
    assert rating.score == 5

    user_rating = await get_user_rating(session, user2.id, rec.id)
    assert user_rating == 5

    stats = await get_recommendation_rating_stats(session, rec.id)
    assert stats["avg_score"] == 5.0
    assert stats["count"] == 1

    await rate_recommendation(session, user2.id, rec.id, 4)
    user_rating = await get_user_rating(session, user2.id, rec.id)
    assert user_rating == 4


@pytest.mark.asyncio
async def test_popular_recommendations(session):
    user = await get_or_create_user(session, 777, "reviewer", "Reviewer")
    rec1 = await add_recommendation(session, user.id, "films", "Film A", "", True)
    rec2 = await add_recommendation(session, user.id, "films", "Film B", "", True)
    rec3 = await add_recommendation(session, user.id, "books", "Book A", "", True)

    user2 = await get_or_create_user(session, 778, "rater", "Rater")
    await rate_recommendation(session, user2.id, rec1.id, 5)
    await rate_recommendation(session, user2.id, rec2.id, 3)
    user3 = await get_or_create_user(session, 779, "rater2", "Rater2")
    await rate_recommendation(session, user3.id, rec1.id, 4)

    popular = await get_popular_recommendations(session, limit=5)
    assert len(popular) == 3
    assert popular[0]["rec"].id == rec1.id
    assert popular[0]["avg_score"] == 4.5


@pytest.mark.asyncio
async def test_get_public_recommendations(session):
    user = await get_or_create_user(session, 888, "author", "Author")
    await add_recommendation(session, user.id, "films", "Public Film", "", True)
    await add_recommendation(session, user.id, "books", "Private Book", "", False)

    public = await get_public_recommendations(session)
    assert len(public) == 1
    assert public[0].title == "Public Film"


@pytest.mark.asyncio
async def test_get_statistics(session):
    user = await get_or_create_user(session, 999, "stats_user", "Stats")
    await add_recommendation(session, user.id, "music", "Song A", "", True)
    await add_recommendation(session, user.id, "music", "Song B", "", True)
    await add_recommendation(session, user.id, "music", "Song C", "", False)

    stats = await get_statistics(session, user.id)
    assert stats["total"] == 3
    assert stats["public"] == 2
    assert stats["private"] == 1


@pytest.mark.asyncio
async def test_get_random_recommendation(session):
    user = await get_or_create_user(session, 1000, "rand_user", "Random")
    await add_recommendation(session, user.id, "games", "Game A", "", True)
    await add_recommendation(session, user.id, "games", "Game B", "", True)

    rec = await get_random_recommendation(session, public_only=True)
    assert rec is not None
    assert rec.title in ["Game A", "Game B"]

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(128), nullable=True)
    first_name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    recommendations = relationship("Recommendation", back_populates="author")
    ratings = relationship("Rating", back_populates="user", overlaps="ratings")

    @property
    def display_name(self):
        return self.first_name or self.username or f"ID {self.telegram_id}"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    comment = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    author = relationship("User", back_populates="recommendations")
    ratings = relationship("Rating", back_populates="recommendation", overlaps="ratings")

    __table_args__ = (
        Index("ix_recommendations_is_public_category", "is_public", "category"),
        Index("ix_recommendations_user_id_created_at", "user_id", "created_at"),
    )


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    __table_args__ = (
        UniqueConstraint("user_id", "recommendation_id", name="uq_user_recommendation"),
    )

    user = relationship("User", back_populates="ratings", overlaps="ratings")
    recommendation = relationship("Recommendation", back_populates="ratings")

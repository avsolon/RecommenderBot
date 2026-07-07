"""add_indexes

Revision ID: 859f61546cd9
Revises: 
Create Date: 2026-07-07 17:47:30.545811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '859f61546cd9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_recommendations_category", "recommendations", ["category"])
    op.create_index("ix_recommendations_created_at", "recommendations", ["created_at"])
    op.create_index("ix_recommendations_is_public_category", "recommendations", ["is_public", "category"])
    op.create_index("ix_recommendations_user_id_created_at", "recommendations", ["user_id", "created_at"])
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_recommendation_id", "ratings", ["recommendation_id"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_category")
    op.drop_index("ix_recommendations_created_at")
    op.drop_index("ix_recommendations_is_public_category")
    op.drop_index("ix_recommendations_user_id_created_at")
    op.drop_index("ix_ratings_user_id")
    op.drop_index("ix_ratings_recommendation_id")

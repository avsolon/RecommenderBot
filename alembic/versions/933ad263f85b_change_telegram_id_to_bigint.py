"""change_telegram_id_to_bigint

Revision ID: 933ad263f85b
Revises: 859f61546cd9
Create Date: 2026-07-20 14:45:39.191504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '933ad263f85b'
down_revision: Union[str, None] = '859f61546cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'telegram_id',
                    type_=sa.BigInteger(),
                    existing_type=sa.Integer(),
                    postgresql_using='telegram_id::bigint')


def downgrade() -> None:
    op.alter_column('users', 'telegram_id',
                    type_=sa.Integer(),
                    existing_type=sa.BigInteger(),
                    postgresql_using='telegram_id::integer')

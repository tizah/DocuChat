"""user_id NOT NULL on documents and conversations

Revision ID: a1b2c3d4e5f6
Revises: 7f9546382ddb
Create Date: 2026-05-15 12:00:00.000000

Closes the orphan-row hole on Document and Conversation. Orphans (user_id IS NULL)
predate auth and can't be reassigned an owner — they're deleted as part of upgrade.
Chunks and messages cascade via existing FKs.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7f9546382ddb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM documents WHERE user_id IS NULL")
    op.execute("DELETE FROM conversations WHERE user_id IS NULL")

    with op.batch_alter_table("documents") as batch:
        batch.alter_column("user_id", existing_type=sa.String(length=36), nullable=False)
    with op.batch_alter_table("conversations") as batch:
        batch.alter_column("user_id", existing_type=sa.String(length=36), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.alter_column("user_id", existing_type=sa.String(length=36), nullable=True)
    with op.batch_alter_table("conversations") as batch:
        batch.alter_column("user_id", existing_type=sa.String(length=36), nullable=True)

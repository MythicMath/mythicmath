#!/usr/bin/env python
"""add google_sub to users

Revision ID: a3a8f5b5f6d1
Revises: 7b6c2e6b0f4d
Create Date: 2026-04-21 00:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3a8f5b5f6d1"
down_revision = "7b6c2e6b0f4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("google_sub", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint("uq_users_google_sub", ["google_sub"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_google_sub", type_="unique")
        batch_op.drop_column("google_sub")

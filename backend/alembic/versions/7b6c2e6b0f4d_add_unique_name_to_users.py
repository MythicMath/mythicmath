#!/usr/bin/env python
"""add unique constraint to users.name

Revision ID: 7b6c2e6b0f4d
Revises: 64776d5e38bf
Create Date: 2026-03-13 00:00:00
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "7b6c2e6b0f4d"
down_revision = "64776d5e38bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_unique_constraint("uq_users_name", ["name"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_name", type_="unique")

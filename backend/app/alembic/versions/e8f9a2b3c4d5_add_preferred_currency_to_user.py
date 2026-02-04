"""add_preferred_currency_to_user

Revision ID: e8f9a2b3c4d5
Revises: 68a5bc7ca648
Create Date: 2026-02-03 12:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f9a2b3c4d5"
down_revision = "68a5bc7ca648"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "preferred_currency",
            sqlmodel.sql.sqltypes.AutoString(length=3),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("user", "preferred_currency")

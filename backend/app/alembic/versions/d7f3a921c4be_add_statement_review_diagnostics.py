"""add review diagnostics fields to card_statement

Revision ID: d7f3a921c4be
Revises: b2f4a8c91d3e
Create Date: 2026-02-11 13:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d7f3a921c4be"
down_revision = "b2f4a8c91d3e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "card_statement",
        sa.Column("review_trigger", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "card_statement",
        sa.Column("review_details", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("card_statement", "review_details")
    op.drop_column("card_statement", "review_trigger")

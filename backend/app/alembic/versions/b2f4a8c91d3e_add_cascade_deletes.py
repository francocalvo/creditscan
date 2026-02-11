"""add cascade deletes to foreign keys

Revision ID: b2f4a8c91d3e
Revises: a8ee30575e0c
Create Date: 2026-02-11 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2f4a8c91d3e"
down_revision = "a8ee30575e0c"
branch_labels = None
depends_on = None


def upgrade():
    # transaction.statement_id -> card_statement.id CASCADE
    op.drop_constraint(
        "transaction_statement_id_fkey", "transaction", type_="foreignkey"
    )
    op.create_foreign_key(
        "transaction_statement_id_fkey",
        "transaction",
        "card_statement",
        ["statement_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # payment.statement_id -> card_statement.id CASCADE
    op.drop_constraint("payment_statement_id_fkey", "payment", type_="foreignkey")
    op.create_foreign_key(
        "payment_statement_id_fkey",
        "payment",
        "card_statement",
        ["statement_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # transaction_tags.transaction_id -> transaction.id CASCADE
    op.drop_constraint(
        "transaction_tags_transaction_id_fkey",
        "transaction_tags",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "transaction_tags_transaction_id_fkey",
        "transaction_tags",
        "transaction",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # transaction_tags.tag_id -> tags.tag_id CASCADE
    op.drop_constraint(
        "transaction_tags_tag_id_fkey", "transaction_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "transaction_tags_tag_id_fkey",
        "transaction_tags",
        "tags",
        ["tag_id"],
        ["tag_id"],
        ondelete="CASCADE",
    )

    # upload_job.statement_id -> card_statement.id SET NULL
    op.drop_constraint("upload_job_statement_id_fkey", "upload_job", type_="foreignkey")
    op.create_foreign_key(
        "upload_job_statement_id_fkey",
        "upload_job",
        "card_statement",
        ["statement_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    # Revert all foreign keys to default (NO ACTION)
    op.drop_constraint("upload_job_statement_id_fkey", "upload_job", type_="foreignkey")
    op.create_foreign_key(
        "upload_job_statement_id_fkey",
        "upload_job",
        "card_statement",
        ["statement_id"],
        ["id"],
    )

    op.drop_constraint(
        "transaction_tags_tag_id_fkey", "transaction_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "transaction_tags_tag_id_fkey",
        "transaction_tags",
        "tags",
        ["tag_id"],
        ["tag_id"],
    )

    op.drop_constraint(
        "transaction_tags_transaction_id_fkey",
        "transaction_tags",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "transaction_tags_transaction_id_fkey",
        "transaction_tags",
        "transaction",
        ["transaction_id"],
        ["id"],
    )

    op.drop_constraint("payment_statement_id_fkey", "payment", type_="foreignkey")
    op.create_foreign_key(
        "payment_statement_id_fkey",
        "payment",
        "card_statement",
        ["statement_id"],
        ["id"],
    )

    op.drop_constraint(
        "transaction_statement_id_fkey", "transaction", type_="foreignkey"
    )
    op.create_foreign_key(
        "transaction_statement_id_fkey",
        "transaction",
        "card_statement",
        ["statement_id"],
        ["id"],
    )

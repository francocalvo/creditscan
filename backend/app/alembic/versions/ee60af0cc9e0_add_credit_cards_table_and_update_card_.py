"""add_credit_cards_table_and_update_card_statements

Revision ID: ee60af0cc9e0
Revises: 9fae62a4aafd
Create Date: 2025-11-02 21:28:58.677579

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "ee60af0cc9e0"
down_revision = "9fae62a4aafd"
branch_labels = None
depends_on = None


def upgrade():
    # Create the credit_card table with enum type
    op.create_table(
        "credit_card",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bank", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "brand",
            sa.Enum(
                "VISA", "MASTERCARD", "AMEX", "DISCOVER", "OTHER", name="cardbrand"
            ),
            nullable=False,
        ),
        sa.Column("last4", sqlmodel.sql.sqltypes.AutoString(length=4), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_credit_card_user_id"), "credit_card", ["user_id"], unique=False
    )

    # Add card_id column as NULLABLE first to allow data migration
    op.add_column("card_statement", sa.Column("card_id", sa.Uuid(), nullable=True))

    # Migrate existing data: Create credit cards from card_statement data and link them
    # This uses a raw SQL approach to handle the data migration
    connection = op.get_bind()

    # Get distinct card combinations from card_statement
    result = connection.execute(
        sa.text("""
        SELECT DISTINCT user_id, card_last4, card_brand
        FROM card_statement
        WHERE card_last4 IS NOT NULL
    """)
    )

    # Create credit cards for each unique combination
    for row in result:
        user_id = row[0]
        last4 = row[1]
        original_brand = row[2]  # Keep original value for matching

        # Normalize brand to match enum values for the credit card
        brand_upper = (original_brand or "OTHER").upper()
        if brand_upper not in ("VISA", "MASTERCARD", "AMEX", "DISCOVER"):
            brand_upper = "OTHER"

        # Insert credit card and get its ID
        card_id = connection.execute(
            sa.text("""
            INSERT INTO credit_card (id, user_id, bank, brand, last4)
            VALUES (gen_random_uuid(), :user_id, 'Unknown', :brand, :last4)
            RETURNING id
        """),
            {"user_id": user_id, "brand": brand_upper, "last4": last4},
        ).fetchone()[0]

        # Update card_statement rows to reference this card
        # Match using the original brand value (or NULL)
        if original_brand is None:
            connection.execute(
                sa.text("""
                UPDATE card_statement
                SET card_id = :card_id
                WHERE user_id = :user_id
                AND card_last4 = :last4
                AND card_brand IS NULL
            """),
                {"card_id": card_id, "user_id": user_id, "last4": last4},
            )
        else:
            connection.execute(
                sa.text("""
                UPDATE card_statement
                SET card_id = :card_id
                WHERE user_id = :user_id
                AND card_last4 = :last4
                AND card_brand = :original_brand
            """),
                {
                    "card_id": card_id,
                    "user_id": user_id,
                    "last4": last4,
                    "original_brand": original_brand,
                },
            )

    # Now make card_id NOT NULL since all rows should have values
    op.alter_column("card_statement", "card_id", nullable=False)

    # Create index and foreign key
    op.create_index(
        op.f("ix_card_statement_card_id"), "card_statement", ["card_id"], unique=False
    )
    op.create_foreign_key(None, "card_statement", "credit_card", ["card_id"], ["id"])

    # Drop old columns
    op.drop_column("card_statement", "card_brand")
    op.drop_column("card_statement", "card_last4")


def downgrade():
    # Add back the old columns
    op.add_column(
        "card_statement",
        sa.Column(
            "card_last4", sa.VARCHAR(length=4), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "card_statement",
        sa.Column("card_brand", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    # Populate old columns from credit_card data
    connection = op.get_bind()
    connection.execute(
        sa.text("""
        UPDATE card_statement cs
        SET card_last4 = cc.last4,
            card_brand = cc.brand::text
        FROM credit_card cc
        WHERE cs.card_id = cc.id
    """)
    )

    # Make card_last4 NOT NULL after populating
    op.alter_column("card_statement", "card_last4", nullable=False)

    # Drop foreign key, index, and card_id column
    op.drop_constraint(None, "card_statement", type_="foreignkey")
    op.drop_index(op.f("ix_card_statement_card_id"), table_name="card_statement")
    op.drop_column("card_statement", "card_id")

    # Drop credit_card table and index
    op.drop_index(op.f("ix_credit_card_user_id"), table_name="credit_card")
    op.drop_table("credit_card")

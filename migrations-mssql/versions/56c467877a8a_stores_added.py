"""Stores added

Revision ID: 56c467877a8a
Revises: 0432b60bf493
Create Date: 2024-01-22 18:38:53.266716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "56c467877a8a"
down_revision = "0432b60bf493"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=True),
        sa.Column("address", sa.String(length=128), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("stores")
    # ### end Alembic commands ###

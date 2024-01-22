"""Initial version

Revision ID: 0432b60bf493
Revises: 
Create Date: 2024-01-19 17:22:47.373550

"""
from alembic import op
import sqlalchemy as sa

from os import getenv
from passlib.hash import pbkdf2_sha256
from rent_a_car.services.user import UserRole

ADMIN_EMAIL = getenv("ADMIN_EMAIL") or "admin@rentacar.com"
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD") or "admin"
ADMIN_NAME = getenv("ADMIN_NAME") or "Administrator"

# revision identifiers, used by Alembic.
revision = "0432b60bf493"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    users_table = op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=60), nullable=True),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("role", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.bulk_insert(
        users_table,
        [
            {
                "email": ADMIN_EMAIL,
                "password": pbkdf2_sha256.hash(ADMIN_PASSWORD),
                "name": ADMIN_NAME,
                "role": UserRole.ADMIN.value,
            }
        ],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    # ### end Alembic commands ###

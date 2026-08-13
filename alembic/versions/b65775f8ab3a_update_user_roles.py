"""update user roles

Revision ID: b65775f8ab3a
Revises: b86e8cbd5d5d
Create Date: 2026-08-13 18:56:25.502839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b65775f8ab3a'
down_revision: Union[str, Sequence[str], None] = 'b86e8cbd5d5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # First allow both the old and new values
    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN role
        ENUM('user', 'client', 'freelancer', 'admin')
        NOT NULL
        """
    )

    # Convert existing users into clients
    op.execute(
        """
        UPDATE users
        SET role = 'client'
        WHERE role = 'user'
        """
    )

    # Finally remove the old 'user' role
    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN role
        ENUM('client', 'freelancer', 'admin')
        NOT NULL
        """
    )
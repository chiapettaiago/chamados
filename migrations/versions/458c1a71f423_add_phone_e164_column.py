"""add phone_e164 column

Revision ID: 458c1a71f423
Revises: 9056094ac1f5
Create Date: 2025-08-08 12:07:45.827927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '458c1a71f423'
down_revision = '9056094ac1f5'
branch_labels = None
depends_on = None


def upgrade():
    # No-op: coluna já adicionada na revisão 9056094ac1f5
    pass


def downgrade():
    # No-op correspondente
    pass

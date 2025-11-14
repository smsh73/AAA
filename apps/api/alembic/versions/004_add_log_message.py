"""add log message

Revision ID: 004_add_log_message
Revises: 478d6db4f74b
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_log_message'
down_revision = '478d6db4f74b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('data_collection_logs', sa.Column('log_message', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('data_collection_logs', 'log_message')


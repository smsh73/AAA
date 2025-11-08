"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 모든 테이블 생성
    # 실제 구현은 각 모델 정의에 따라 자동 생성됨
    pass


def downgrade():
    # 모든 테이블 삭제
    pass


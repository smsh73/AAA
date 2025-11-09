"""003_make_company_ticker_nullable

Revision ID: 478d6db4f74b
Revises: 002
Create Date: 2025-11-09 18:11:40.974359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '478d6db4f74b'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Company 모델의 ticker 필드를 nullable로 변경"""
    # 기존 ticker가 NULL인 레코드가 있을 수 있으므로, 먼저 임시 값 설정
    # (실제로는 기존 데이터가 있을 가능성이 낮지만 안전을 위해)
    op.execute("""
        UPDATE companies 
        SET ticker = 'TEMP_' || SUBSTRING(MD5(name_kr::text) FROM 1 FOR 6)
        WHERE ticker IS NULL OR ticker = '';
    """)
    
    # ticker 컬럼의 NOT NULL 제약 조건 제거
    op.alter_column('companies', 'ticker',
                    existing_type=sa.String(length=20),
                    nullable=True,
                    existing_nullable=False)


def downgrade():
    """Company 모델의 ticker 필드를 NOT NULL로 복원"""
    # NULL인 레코드가 있으면 임시 값 설정
    op.execute("""
        UPDATE companies 
        SET ticker = 'TEMP_' || SUBSTRING(MD5(name_kr::text) FROM 1 FOR 6)
        WHERE ticker IS NULL;
    """)
    
    # ticker 컬럼에 NOT NULL 제약 조건 추가
    op.alter_column('companies', 'ticker',
                    existing_type=sa.String(length=20),
                    nullable=False,
                    existing_nullable=True)

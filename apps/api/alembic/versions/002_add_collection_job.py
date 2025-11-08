"""Add collection_job model and update data_collection_log

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # collection_jobs 테이블 생성
    op.create_table(
        'collection_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', postgresql.JSONB, server_default='{}'),
        sa.Column('overall_progress', sa.String(10), server_default='0.0'),
        sa.Column('estimated_completion_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id'], ),
    )
    
    # 인덱스 생성
    op.create_index('idx_collection_jobs_analyst_id', 'collection_jobs', ['analyst_id'])
    op.create_index('idx_collection_jobs_status', 'collection_jobs', ['status'])
    
    # data_collection_logs 테이블에 collection_job_id 컬럼 추가
    op.add_column('data_collection_logs', sa.Column('collection_job_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_data_collection_logs_collection_job_id', 'data_collection_logs', 'collection_jobs', ['collection_job_id'], ['id'])
    op.create_index('idx_data_collection_logs_collection_job_id', 'data_collection_logs', ['collection_job_id'])


def downgrade():
    # 인덱스 삭제
    op.drop_index('idx_data_collection_logs_collection_job_id', table_name='data_collection_logs')
    op.drop_constraint('fk_data_collection_logs_collection_job_id', 'data_collection_logs', type_='foreignkey')
    
    # 컬럼 삭제
    op.drop_column('data_collection_logs', 'collection_job_id')
    
    # 테이블 삭제
    op.drop_index('idx_collection_jobs_status', table_name='collection_jobs')
    op.drop_index('idx_collection_jobs_analyst_id', table_name='collection_jobs')
    op.drop_table('collection_jobs')


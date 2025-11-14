"""create api logs table

Revision ID: 005_create_api_logs
Revises: 004_add_log_message
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_api_logs'
down_revision = '004_add_log_message'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'api_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('query_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('path_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_body', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_body', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('client_ip', sa.String(length=50), nullable=True),
        sa.Column('request_time', sa.Float(), nullable=True),
        sa.Column('db_query_count', sa.Integer(), nullable=True),
        sa.Column('db_query_time', sa.Float(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('function_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('service_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('external_api_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('debug_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feedback_loop', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 인덱스 생성
    op.create_index('idx_api_logs_method', 'api_logs', ['method'])
    op.create_index('idx_api_logs_path', 'api_logs', ['path'])
    op.create_index('idx_api_logs_status_code', 'api_logs', ['status_code'])
    op.create_index('idx_api_logs_user_id', 'api_logs', ['user_id'])
    op.create_index('idx_api_logs_client_ip', 'api_logs', ['client_ip'])
    op.create_index('idx_api_logs_request_id', 'api_logs', ['request_id'])
    op.create_index('idx_api_logs_created_at', 'api_logs', ['created_at'])
    op.create_index('idx_api_logs_user_created', 'api_logs', ['user_id', 'created_at'])
    op.create_index('idx_api_logs_path_method', 'api_logs', ['path', 'method'])
    op.create_index('idx_api_logs_status_code_created', 'api_logs', ['status_code', 'created_at'])


def downgrade():
    op.drop_index('idx_api_logs_status_code_created', table_name='api_logs')
    op.drop_index('idx_api_logs_path_method', table_name='api_logs')
    op.drop_index('idx_api_logs_user_created', table_name='api_logs')
    op.drop_index('idx_api_logs_created_at', table_name='api_logs')
    op.drop_index('idx_api_logs_request_id', table_name='api_logs')
    op.drop_index('idx_api_logs_client_ip', table_name='api_logs')
    op.drop_index('idx_api_logs_user_id', table_name='api_logs')
    op.drop_index('idx_api_logs_status_code', table_name='api_logs')
    op.drop_index('idx_api_logs_path', table_name='api_logs')
    op.drop_index('idx_api_logs_method', table_name='api_logs')
    op.drop_table('api_logs')


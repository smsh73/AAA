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
    # 1. 기본 엔티티 테이블
    op.create_table(
        'analysts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('firm', sa.String(255), nullable=False),
        sa.Column('department', sa.String(255)),
        sa.Column('sector', sa.String(100)),
        sa.Column('experience_years', sa.Integer()),
        sa.Column('email', sa.String(255)),
        sa.Column('profile_url', sa.Text()),
        sa.Column('bio', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_analysts_name', 'analysts', ['name'])

    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ticker', sa.String(20), nullable=False, unique=True),
        sa.Column('name_kr', sa.String(255), nullable=False),
        sa.Column('name_en', sa.String(255)),
        sa.Column('sector', sa.String(100)),
        sa.Column('market_cap', sa.Numeric(20, 2)),
        sa.Column('fundamentals', postgresql.JSONB),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_companies_ticker', 'companies', ['ticker'])

    op.create_table(
        'markets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('region', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # 2. 리포트 관련 테이블
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('market_id', postgresql.UUID(as_uuid=True)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('report_type', sa.String(50)),
        sa.Column('publication_date', sa.Date(), nullable=False),
        sa.Column('source_url', sa.Text()),
        sa.Column('file_path', sa.Text()),
        sa.Column('file_size', sa.Integer()),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('parsed_json', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'])
    )
    op.create_index('idx_reports_analyst_id', 'reports', ['analyst_id'])
    op.create_index('idx_reports_publication_date', 'reports', ['publication_date'])
    op.create_index('idx_reports_status', 'reports', ['status'])

    op.create_table(
        'report_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_type', sa.String(50)),
        sa.Column('title', sa.String(500)),
        sa.Column('content', sa.Text()),
        sa.Column('page_number', sa.Integer()),
        sa.Column('order', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE')
    )
    op.create_index('idx_report_sections_report_id', 'report_sections', ['report_id'])

    op.create_table(
        'extracted_texts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('bbox', postgresql.JSONB),
        sa.Column('confidence', sa.String(10)),
        sa.Column('language', sa.String(10)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'])
    )
    op.create_index('idx_extracted_texts_report_id', 'extracted_texts', ['report_id'])

    op.create_table(
        'extracted_tables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('table_data', postgresql.JSONB, nullable=False),
        sa.Column('bbox', postgresql.JSONB),
        sa.Column('confidence', sa.String(10)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'])
    )
    op.create_index('idx_extracted_tables_report_id', 'extracted_tables', ['report_id'])

    op.create_table(
        'extracted_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('image_path', sa.Text(), nullable=False),
        sa.Column('image_type', sa.String(50)),
        sa.Column('bbox', postgresql.JSONB),
        sa.Column('analysis_result', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'])
    )
    op.create_index('idx_extracted_images_report_id', 'extracted_images', ['report_id'])

    # 3. 예측 및 결과 테이블
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('market_id', postgresql.UUID(as_uuid=True)),
        sa.Column('prediction_type', sa.String(50), nullable=False),
        sa.Column('predicted_value', sa.Numeric(20, 2), nullable=False),
        sa.Column('unit', sa.String(20)),
        sa.Column('period', sa.String(20)),
        sa.Column('reasoning', sa.Text()),
        sa.Column('confidence', sa.String(10)),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'])
    )
    op.create_index('idx_predictions_report_id', 'predictions', ['report_id'])
    op.create_index('idx_predictions_prediction_type', 'predictions', ['prediction_type'])

    op.create_table(
        'actual_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actual_value', sa.Numeric(20, 2), nullable=False),
        sa.Column('unit', sa.String(20)),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('announcement_date', sa.Date()),
        sa.Column('source', sa.String(255)),
        sa.Column('source_url', sa.Text()),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'])
    )
    op.create_index('idx_actual_results_prediction_id', 'actual_results', ['prediction_id'])
    op.create_index('idx_actual_results_company_id', 'actual_results', ['company_id'])
    op.create_index('idx_actual_results_period', 'actual_results', ['period'])

    # 4. 평가 관련 테이블
    op.create_table(
        'evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('report_id', postgresql.UUID(as_uuid=True)),
        sa.Column('evaluation_period', sa.String(20), nullable=False),
        sa.Column('evaluation_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('final_score', sa.Numeric(10, 2)),
        sa.Column('ai_quantitative_score', sa.Numeric(10, 2)),
        sa.Column('sns_market_score', sa.Numeric(10, 2)),
        sa.Column('expert_survey_score', sa.Numeric(10, 2)),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'])
    )
    op.create_index('idx_evaluations_analyst_id', 'evaluations', ['analyst_id'])
    op.create_index('idx_evaluations_evaluation_period', 'evaluations', ['evaluation_period'])
    op.create_index('idx_evaluations_status', 'evaluations', ['status'])

    op.create_table(
        'evaluation_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score_type', sa.String(50), nullable=False),
        sa.Column('score_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('weight', sa.Numeric(5, 4)),
        sa.Column('details', postgresql.JSONB),
        sa.Column('reasoning', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE')
    )
    op.create_index('idx_evaluation_scores_evaluation_id', 'evaluation_scores', ['evaluation_id'])
    op.create_index('idx_evaluation_scores_score_type', 'evaluation_scores', ['score_type'])

    op.create_table(
        'evaluation_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('report_type', sa.String(50), server_default='detailed_evaluation'),
        sa.Column('report_structure', postgresql.JSONB),
        sa.Column('report_content', postgresql.JSONB),
        sa.Column('report_summary', sa.Text()),
        sa.Column('data_sources_count', sa.Integer(), server_default='0'),
        sa.Column('verification_status', sa.String(20), server_default='pending'),
        sa.Column('report_quality_score', sa.Numeric(5, 4)),
        sa.Column('generated_by', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'])
    )
    op.create_index('idx_evaluation_reports_evaluation_id', 'evaluation_reports', ['evaluation_id'])
    op.create_index('idx_evaluation_reports_analyst_id', 'evaluation_reports', ['analyst_id'])

    # 5. 스코어카드 및 수상 테이블
    op.create_table(
        'scorecards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('market_id', postgresql.UUID(as_uuid=True)),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('final_score', sa.Numeric(10, 2), nullable=False),
        sa.Column('ranking', sa.Integer()),
        sa.Column('scorecard_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'])
    )
    op.create_index('idx_scorecards_analyst_id', 'scorecards', ['analyst_id'])
    op.create_index('idx_scorecards_period', 'scorecards', ['period'])
    op.create_index('idx_scorecards_final_score', 'scorecards', ['final_score'])
    op.create_index('idx_scorecards_ranking', 'scorecards', ['ranking'])

    op.create_table(
        'awards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('scorecard_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('award_type', sa.String(20), nullable=False),
        sa.Column('award_category', sa.String(50), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['scorecard_id'], ['scorecards.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id'])
    )
    op.create_index('idx_awards_scorecard_id', 'awards', ['scorecard_id'])
    op.create_index('idx_awards_analyst_id', 'awards', ['analyst_id'])
    op.create_index('idx_awards_award_category', 'awards', ['award_category'])
    op.create_index('idx_awards_period', 'awards', ['period'])
    op.create_index('idx_awards_rank', 'awards', ['rank'])

    # 6. 데이터 수집 테이블
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_name', sa.String(255), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.String(500)),
        sa.Column('reliability', sa.String(20)),
        sa.Column('update_frequency', sa.String(50)),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE'),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_data_sources_source_type', 'data_sources', ['source_type'])
    op.create_index('idx_data_sources_is_active', 'data_sources', ['is_active'])

    op.create_table(
        'data_collection_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('collection_type', sa.String(50), nullable=False),
        sa.Column('prompt_template_id', sa.String(100)),
        sa.Column('perplexity_request', postgresql.JSONB),
        sa.Column('perplexity_response', postgresql.JSONB),
        sa.Column('collected_data', postgresql.JSONB),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('collection_time', sa.Float()),
        sa.Column('token_usage', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['analyst_id'], ['analysts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'])
    )
    op.create_index('idx_data_collection_logs_analyst_id', 'data_collection_logs', ['analyst_id'])
    op.create_index('idx_data_collection_logs_collection_type', 'data_collection_logs', ['collection_type'])
    op.create_index('idx_data_collection_logs_status', 'data_collection_logs', ['status'])

    # 7. 템플릿 테이블
    op.create_table(
        'prompt_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('template_name', sa.String(255), nullable=False, unique=True),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('kpi_type', sa.String(50)),
        sa.Column('prompt_content', sa.Text(), nullable=False),
        sa.Column('input_schema', postgresql.JSONB),
        sa.Column('output_schema', postgresql.JSONB),
        sa.Column('max_input_tokens', sa.Integer(), server_default='1000000'),
        sa.Column('max_output_tokens', sa.Integer(), server_default='100000'),
        sa.Column('version', sa.String(20), server_default='1.0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_prompt_templates_template_type', 'prompt_templates', ['template_type'])
    op.create_index('idx_prompt_templates_kpi_type', 'prompt_templates', ['kpi_type'])
    op.create_index('idx_prompt_templates_is_active', 'prompt_templates', ['is_active'])


def downgrade():
    # 역순으로 테이블 삭제 (외래 키 의존성 고려)
    
    # 7. 템플릿 테이블
    op.drop_index('idx_prompt_templates_is_active', table_name='prompt_templates')
    op.drop_index('idx_prompt_templates_kpi_type', table_name='prompt_templates')
    op.drop_index('idx_prompt_templates_template_type', table_name='prompt_templates')
    op.drop_table('prompt_templates')

    # 6. 데이터 수집 테이블
    op.drop_index('idx_data_collection_logs_status', table_name='data_collection_logs')
    op.drop_index('idx_data_collection_logs_collection_type', table_name='data_collection_logs')
    op.drop_index('idx_data_collection_logs_analyst_id', table_name='data_collection_logs')
    op.drop_table('data_collection_logs')

    op.drop_index('idx_data_sources_is_active', table_name='data_sources')
    op.drop_index('idx_data_sources_source_type', table_name='data_sources')
    op.drop_table('data_sources')

    # 5. 스코어카드 및 수상 테이블
    op.drop_index('idx_awards_rank', table_name='awards')
    op.drop_index('idx_awards_period', table_name='awards')
    op.drop_index('idx_awards_award_category', table_name='awards')
    op.drop_index('idx_awards_analyst_id', table_name='awards')
    op.drop_index('idx_awards_scorecard_id', table_name='awards')
    op.drop_table('awards')

    op.drop_index('idx_scorecards_ranking', table_name='scorecards')
    op.drop_index('idx_scorecards_final_score', table_name='scorecards')
    op.drop_index('idx_scorecards_period', table_name='scorecards')
    op.drop_index('idx_scorecards_analyst_id', table_name='scorecards')
    op.drop_table('scorecards')

    # 4. 평가 관련 테이블
    op.drop_index('idx_evaluation_reports_analyst_id', table_name='evaluation_reports')
    op.drop_index('idx_evaluation_reports_evaluation_id', table_name='evaluation_reports')
    op.drop_table('evaluation_reports')

    op.drop_index('idx_evaluation_scores_score_type', table_name='evaluation_scores')
    op.drop_index('idx_evaluation_scores_evaluation_id', table_name='evaluation_scores')
    op.drop_table('evaluation_scores')

    op.drop_index('idx_evaluations_status', table_name='evaluations')
    op.drop_index('idx_evaluations_evaluation_period', table_name='evaluations')
    op.drop_index('idx_evaluations_analyst_id', table_name='evaluations')
    op.drop_table('evaluations')

    # 3. 예측 및 결과 테이블
    op.drop_index('idx_actual_results_period', table_name='actual_results')
    op.drop_index('idx_actual_results_company_id', table_name='actual_results')
    op.drop_index('idx_actual_results_prediction_id', table_name='actual_results')
    op.drop_table('actual_results')

    op.drop_index('idx_predictions_prediction_type', table_name='predictions')
    op.drop_index('idx_predictions_report_id', table_name='predictions')
    op.drop_table('predictions')

    # 2. 리포트 관련 테이블
    op.drop_index('idx_extracted_images_report_id', table_name='extracted_images')
    op.drop_table('extracted_images')

    op.drop_index('idx_extracted_tables_report_id', table_name='extracted_tables')
    op.drop_table('extracted_tables')

    op.drop_index('idx_extracted_texts_report_id', table_name='extracted_texts')
    op.drop_table('extracted_texts')

    op.drop_index('idx_report_sections_report_id', table_name='report_sections')
    op.drop_table('report_sections')

    op.drop_index('idx_reports_status', table_name='reports')
    op.drop_index('idx_reports_publication_date', table_name='reports')
    op.drop_index('idx_reports_analyst_id', table_name='reports')
    op.drop_table('reports')

    # 1. 기본 엔티티 테이블
    op.drop_table('markets')
    op.drop_index('idx_companies_ticker', table_name='companies')
    op.drop_table('companies')
    op.drop_index('idx_analysts_name', table_name='analysts')
    op.drop_table('analysts')

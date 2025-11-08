"""
Report processing tasks
"""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
from uuid import UUID


@celery_app.task(name="parse_report")
def parse_report_task(report_id: str, file_path: str):
    """리포트 파싱 작업"""
    db = SessionLocal()
    try:
        agent = ReportParsingAgent(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # result = await agent.parse_report(UUID(report_id), file_path)
        return {"status": "completed", "report_id": report_id}
    finally:
        db.close()


@celery_app.task(name="extract_predictions")
def extract_predictions_task(report_id: str):
    """예측 정보 추출 작업"""
    db = SessionLocal()
    try:
        # 예측 정보 추출 로직
        return {"status": "completed", "report_id": report_id}
    finally:
        db.close()


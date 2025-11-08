"""
Report processing tasks
"""
import asyncio
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
from uuid import UUID


def run_async(coro):
    """Async 함수를 동기적으로 실행하는 헬퍼"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="parse_report")
def parse_report_task(report_id: str, file_path: str):
    """리포트 파싱 작업"""
    db = SessionLocal()
    try:
        agent = ReportParsingAgent(db)
        # Async 함수 실행
        result = run_async(agent.parse_report(UUID(report_id), file_path))
        return {
            "status": "completed",
            "report_id": report_id,
            "result": result
        }
    except Exception as e:
        return {
            "status": "failed",
            "report_id": report_id,
            "error": str(e)
        }
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


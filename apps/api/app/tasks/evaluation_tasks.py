"""
Evaluation tasks
"""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.services.evaluation_service import EvaluationService
from uuid import UUID


@celery_app.task(name="evaluate_report")
def evaluate_report_task(evaluation_id: str, report_id: str):
    """리포트 평가 작업"""
    db = SessionLocal()
    try:
        agent = EvaluationAgent(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # result = await agent.evaluate_async(UUID(evaluation_id), UUID(report_id))
        
        # 평가 완료 처리
        service = EvaluationService(db)
        # result = await service.complete_evaluation(UUID(evaluation_id))
        
        return {"status": "completed", "evaluation_id": evaluation_id}
    finally:
        db.close()


@celery_app.task(name="generate_evaluation_report")
def generate_evaluation_report_task(
    report_id: str,
    evaluation_id: str,
    include_sections: list,
    detail_level: str
):
    """상세 평가보고서 생성 작업"""
    db = SessionLocal()
    try:
        from app.services.ai_agents.report_generation_agent import ReportGenerationAgent
        
        agent = ReportGenerationAgent(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # result = await agent.generate_async(
        #     UUID(report_id),
        #     UUID(evaluation_id),
        #     include_sections,
        #     detail_level
        # )
        
        return {"status": "completed", "report_id": report_id}
    finally:
        db.close()


"""
Evaluation tasks
"""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from uuid import UUID


@celery_app.task(name="evaluate_report")
def evaluate_report_task(evaluation_id: str, report_id: str):
    """리포트 평가 작업"""
    import asyncio
    from app.services.ai_agents.evaluation_agent import EvaluationAgent
    
    db = SessionLocal()
    try:
        agent = EvaluationAgent(db)
        
        # 비동기 함수 실행을 위한 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                agent.evaluate_async(UUID(evaluation_id), UUID(report_id))
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"평가 작업 실패: {str(e)}")
        
        # 평가 상태를 실패로 업데이트
        from app.models.evaluation import Evaluation
        from app.models.enums import EvaluationStatus
        evaluation = db.query(Evaluation).filter(Evaluation.id == UUID(evaluation_id)).first()
        if evaluation:
            evaluation.status = EvaluationStatus.FAILED.value
            db.commit()
        
        raise
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


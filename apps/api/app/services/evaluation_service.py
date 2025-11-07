"""
Evaluation service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationResponse
from app.services.ai_agents.evaluation_agent import EvaluationAgent


class EvaluationService:
    """평가 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluation_agent = EvaluationAgent()

    async def start_evaluation(self, report_id: UUID) -> EvaluationResponse:
        """평가 시작"""
        evaluation = Evaluation(
            report_id=report_id,
            evaluation_period=datetime.now().strftime("%Y-Q%q"),
            evaluation_date=datetime.now().date(),
            status="processing"
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        # 비동기 평가 시작 (Celery 작업)
        # await self.evaluation_agent.evaluate_async(evaluation.id, report_id)

        return EvaluationResponse(
            evaluation_id=evaluation.id,
            status="processing",
            estimated_completion_time=datetime.utcnow() + timedelta(hours=1)
        )


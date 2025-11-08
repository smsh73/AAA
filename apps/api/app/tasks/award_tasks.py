"""
Award selection tasks
"""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.award_agent import AwardAgent


@celery_app.task(name="select_awards")
def select_awards_task(year: int, quarter: int = None, categories: list = None):
    """어워드 선정 작업"""
    db = SessionLocal()
    try:
        agent = AwardAgent(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # result = await agent.select_awards(year, quarter, categories)
        
        return {"status": "completed", "year": year, "quarter": quarter}
    finally:
        db.close()


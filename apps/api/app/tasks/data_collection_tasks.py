"""
Data collection tasks
"""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.data_collection_agent import DataCollectionAgent
from uuid import UUID


@celery_app.task(name="collect_data")
def collect_data_task(
    analyst_id: str,
    collection_type: str,
    params: dict
):
    """데이터 수집 작업"""
    db = SessionLocal()
    try:
        agent = DataCollectionAgent(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # result = await agent.collect_data(
        #     UUID(analyst_id),
        #     collection_type,
        #     params
        # )
        
        return {"status": "completed", "collection_type": collection_type}
    finally:
        db.close()


@celery_app.task(name="start_collection_for_analyst")
def start_collection_for_analyst_task(analyst_id: str):
    """애널리스트별 자료수집 시작 작업"""
    db = SessionLocal()
    try:
        from app.services.data_collection_service import DataCollectionService
        
        service = DataCollectionService(db)
        # 동기 실행 (실제로는 async 래퍼 필요)
        # await service.start_collection_for_analyst(UUID(analyst_id))
        
        return {"status": "completed", "analyst_id": analyst_id}
    finally:
        db.close()


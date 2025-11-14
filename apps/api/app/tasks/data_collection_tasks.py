"""
Data collection tasks
"""
import asyncio
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.ai_agents.data_collection_agent import DataCollectionAgent
from app.models.collection_job import CollectionJob
from app.models.data_collection_log import DataCollectionLog
from uuid import UUID
from datetime import datetime
from typing import Dict, Any


def run_async(coro):
    """Async 함수를 동기적으로 실행하는 헬퍼"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _check_job_completion(db: SessionLocal, job: CollectionJob):
    """작업 완료 여부를 확인하고 상태 업데이트"""
    if job.status not in ["running", "pending"]:
        return
    
    # 모든 타입의 작업이 완료되었는지 확인
    all_completed = True
    for collection_type in job.collection_types:
        if collection_type not in job.progress:
            all_completed = False
            break
        
        progress = job.progress[collection_type]
        total = progress.get("total", 0)
        completed = progress.get("completed", 0)
        failed = progress.get("failed", 0)
        
        # 총 작업 수가 0이거나, 완료+실패가 총 작업 수와 같지 않으면 아직 진행 중
        if total == 0 or (completed + failed) < total:
            all_completed = False
            break
    
    if all_completed:
        job.status = "completed"
        job.completed_at = datetime.now()
        
        # 전체 진행률을 100%로 설정
        job.overall_progress = "100.0"


@celery_app.task(name="collect_data")
def collect_data_task(
    analyst_id: str,
    collection_type: str,
    params: dict,
    collection_job_id: str = None
):
    """데이터 수집 작업"""
    db = SessionLocal()
    try:
        agent = DataCollectionAgent(db)
        
        # Async 함수 실행
        job_uuid = UUID(collection_job_id) if collection_job_id else None
        result = run_async(agent.collect_data(
            UUID(analyst_id),
            collection_type,
            params,
            collection_job_id=job_uuid
        ))
        
        # CollectionJob 진행 상황 업데이트 및 완료 체크
        if collection_job_id:
            job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
            if job:
                if collection_type not in job.progress:
                    job.progress[collection_type] = {"total": 0, "completed": 0, "failed": 0}
                
                if result.get("status") == "success":
                    job.progress[collection_type]["completed"] = job.progress[collection_type].get("completed", 0) + 1
                else:
                    job.progress[collection_type]["failed"] = job.progress[collection_type].get("failed", 0) + 1
                
                # 전체 진행률 계산
                total_tasks = sum(p.get("total", 0) for p in job.progress.values())
                completed_tasks = sum(p.get("completed", 0) for p in job.progress.values())
                overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                job.overall_progress = f"{overall_progress:.1f}"
                
                # 작업 완료 체크
                _check_job_completion(db, job)
                
                db.commit()
        
        return {"status": "completed", "collection_type": collection_type, "result": result}
    except Exception as e:
        # 에러 발생 시 CollectionJob 업데이트
        if collection_job_id:
            try:
                job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
                if job:
                    if collection_type not in job.progress:
                        job.progress[collection_type] = {"total": 0, "completed": 0, "failed": 0}
                    job.progress[collection_type]["failed"] = job.progress[collection_type].get("failed", 0) + 1
                    
                    # 전체 진행률 계산
                    total_tasks = sum(p.get("total", 0) for p in job.progress.values())
                    completed_tasks = sum(p.get("completed", 0) for p in job.progress.values())
                    overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                    job.overall_progress = f"{overall_progress:.1f}"
                    
                    # 작업 완료 체크
                    _check_job_completion(db, job)
                    
                    db.commit()
            except Exception as db_error:
                # DB 업데이트 실패해도 원래 에러는 전파
                pass
        raise
    finally:
        db.close()


@celery_app.task(name="check_job_completion")
def check_job_completion_task(collection_job_id: str):
    """작업 완료 여부를 주기적으로 확인하는 태스크"""
    db = SessionLocal()
    try:
        job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
        if not job:
            return {"status": "not_found"}
        
        if job.status in ["completed", "failed"]:
            return {"status": job.status, "message": "Job already finished"}
        
        # 완료 여부 확인
        _check_job_completion(db, job)
        
        # 아직 완료되지 않았다면 다시 스케줄링
        if job.status == "running":
            check_job_completion_task.apply_async(
                args=[collection_job_id],
                countdown=60  # 1분 후 다시 확인
            )
        
        db.commit()
        return {"status": job.status, "progress": job.overall_progress}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="start_collection_for_analyst")
def start_collection_for_analyst_task(analyst_id: str):
    """애널리스트별 자료수집 시작 작업"""
    db = SessionLocal()
    try:
        from app.services.data_collection_service import DataCollectionService
        
        service = DataCollectionService(db)
        # Async 함수 실행
        run_async(service.start_collection_for_analyst(UUID(analyst_id)))
        
        return {"status": "completed", "analyst_id": analyst_id}
    finally:
        db.close()


@celery_app.task(name="start_collection_job")
def start_collection_job_task(collection_job_id: str):
    """데이터 수집 작업 실행"""
    db = SessionLocal()
    try:
        from app.models.analyst import Analyst
        from app.models.report import Report
        from app.services.ai_agents.data_collection_agent import DataCollectionAgent
        
        job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
        if not job:
            return {"status": "failed", "error": "Job not found"}
        
        # 작업 상태를 running으로 변경
        job.status = "running"
        job.started_at = datetime.now()
        db.commit()
        
        analyst = db.query(Analyst).filter(Analyst.id == job.analyst_id).first()
        if not analyst:
            job.status = "failed"
            job.error_message = "Analyst not found"
            db.commit()
            return {"status": "failed", "error": "Analyst not found"}
        
        # 기간 내 리포트 조회
        reports = db.query(Report).filter(
            Report.analyst_id == job.analyst_id,
            Report.publication_date >= job.start_date,
            Report.publication_date <= job.end_date
        ).all()
        
        collection_agent = DataCollectionAgent(db)
        
        # 각 수집 타입별로 작업 실행
        for collection_type in job.collection_types:
            if collection_type not in job.progress:
                job.progress[collection_type] = {"total": 0, "completed": 0, "failed": 0}
            
            # 리포트별로 데이터 수집
            for report in reports:
                params = {}
                
                if collection_type in ["target_price", "performance"]:
                    if not report.company_id:
                        continue
                    params = {
                        "company_id": str(report.company_id),
                        "report_id": str(report.id),
                    }
                elif collection_type in ["sns", "media"]:
                    params = {
                        "analyst_name": analyst.name,
                        "securities_firm": analyst.firm,
                        "report_title": report.title,
                        "report_date": report.publication_date.isoformat() if report.publication_date else None,
                    }
                
                if params:
                    job.progress[collection_type]["total"] = job.progress[collection_type].get("total", 0) + 1
                    db.commit()
                    
                    # Celery 태스크로 비동기 실행
                    collect_data_task.delay(
                        str(job.analyst_id),
                        collection_type,
                        params,
                        collection_job_id=str(job.id)
                    )
        
        # 작업 완료 체크 태스크 스케줄링 (5분 후)
        check_job_completion_task.apply_async(
            args=[collection_job_id],
            countdown=300  # 5분 후 실행
        )
        
        return {"status": "started", "collection_job_id": collection_job_id}
    except Exception as e:
        job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="start_comprehensive_collection")
def start_comprehensive_collection_task(collection_job_id: str):
    """통합 자료수집 작업 실행"""
    db = SessionLocal()
    try:
        from app.services.data_collection_service import DataCollectionService
        
        job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
        if not job:
            return {"status": "failed", "error": "Job not found"}
        
        # 작업 상태를 running으로 변경
        job.status = "running"
        job.started_at = datetime.now()
        db.commit()
        
        service = DataCollectionService(db)
        
        # 통합 수집 실행
        result = run_async(service.start_comprehensive_collection(
            analyst_id=job.analyst_id,
            collection_types=job.collection_types,
            start_date=job.start_date.date(),
            end_date=job.end_date.date(),
            collection_job_id=job.id
        ))
        
        # 작업 완료
        job.status = "completed"
        job.completed_at = datetime.now()
        job.overall_progress = "100.0"
        db.commit()
        
        return {"status": "completed", "result": result}
    except Exception as e:
        job = db.query(CollectionJob).filter(CollectionJob.id == UUID(collection_job_id)).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()


"""
Agents router
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.services.ai_agents.award_agent import AwardAgent
from app.services.ai_agents.report_generation_agent import ReportGenerationAgent
from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
from app.services.ai_agents.company_verification_agent import CompanyVerificationAgent
from app.services.ai_agents.performance_verification_agent import PerformanceVerificationAgent
from app.services.ai_agents.stock_tracking_agent import StockTrackingAgent
from app.services.ai_agents.orchestrator_agent import OrchestratorAgent
from app.services.ai_agents.portfolio_analysis_agent import PortfolioAnalysisAgent
from app.tasks.evaluation_tasks import run_evaluation_task
from app.tasks.award_tasks import run_award_task

router = APIRouter()


class AgentRunRequest(BaseModel):
    analyst_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    period: Optional[str] = None
    metrics: Optional[list] = None
    params: Optional[Dict[str, Any]] = None


class EvaluationAgentRequest(BaseModel):
    analyst_id: UUID
    period: str
    metrics: Optional[list] = None


class AwardAgentRequest(BaseModel):
    year: int
    quarter: Optional[int] = None
    categories: list[str]


class ReportGenerationRequest(BaseModel):
    company_id: Optional[UUID] = None
    sector_id: Optional[UUID] = None
    report_type: str
    depth_level: str = "medium"
    data_sources: Optional[list] = None


class ReportParsingRequest(BaseModel):
    report_id: UUID
    report_type: str
    source_format: str = "pdf"


class CompanyVerificationRequest(BaseModel):
    company_id: UUID
    verification_fields: Optional[list] = None
    sources: Optional[list] = None


class PerformanceVerificationRequest(BaseModel):
    analyst_id: UUID
    company_id: UUID
    period: str
    metrics: Optional[list] = None


class StockTrackingRequest(BaseModel):
    recommendation_id: UUID
    tracking_period: str
    benchmark_id: Optional[UUID] = None


class OrchestratorRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    quality_threshold: float = 0.8


class PortfolioAnalysisRequest(BaseModel):
    portfolio_id: UUID
    holdings: list
    constraints: Optional[Dict[str, Any]] = None
    target_return: Optional[float] = None


@router.post("/evaluation/run")
async def run_evaluation_agent(
    request: EvaluationAgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """평가 에이전트 실행"""
    try:
        # Celery 작업으로 비동기 실행
        task = run_evaluation_task.delay(
            str(request.analyst_id),
            request.period,
            request.metrics or []
        )
        return {
            "task_id": task.id,
            "status": "started",
            "message": "평가 작업이 시작되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 에이전트 실행 실패: {str(e)}")


@router.post("/award/run")
async def run_award_agent(
    request: AwardAgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """어워드 에이전트 실행"""
    try:
        # Celery 작업으로 비동기 실행
        task = run_award_task.delay(
            request.year,
            request.quarter,
            request.categories
        )
        return {
            "task_id": task.id,
            "status": "started",
            "message": "어워드 선정 작업이 시작되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"어워드 에이전트 실행 실패: {str(e)}")


@router.post("/report/generate")
async def run_report_generation_agent(
    request: ReportGenerationRequest,
    db: Session = Depends(get_db)
):
    """리포트 생성 에이전트 실행"""
    try:
        agent = ReportGenerationAgent(db)
        result = await agent.generate_report(
            company_id=request.company_id,
            sector_id=request.sector_id,
            report_type=request.report_type,
            depth_level=request.depth_level,
            data_sources=request.data_sources or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")


@router.post("/report/parse")
async def run_report_parsing_agent(
    request: ReportParsingRequest,
    db: Session = Depends(get_db)
):
    """리포트 파싱 에이전트 실행"""
    try:
        agent = ReportParsingAgent(db)
        result = await agent.parse_report(
            report_id=request.report_id,
            report_type=request.report_type,
            source_format=request.source_format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 파싱 실패: {str(e)}")


@router.post("/company/verify")
async def run_company_verification_agent(
    request: CompanyVerificationRequest,
    db: Session = Depends(get_db)
):
    """기업정보 검증 에이전트 실행"""
    try:
        agent = CompanyVerificationAgent(db)
        result = await agent.verify_company(
            company_id=request.company_id,
            verification_fields=request.verification_fields or [],
            sources=request.sources or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기업정보 검증 실패: {str(e)}")


@router.post("/performance/verify")
async def run_performance_verification_agent(
    request: PerformanceVerificationRequest,
    db: Session = Depends(get_db)
):
    """실적 검증 에이전트 실행"""
    try:
        agent = PerformanceVerificationAgent(db)
        result = await agent.verify_performance(
            analyst_id=request.analyst_id,
            company_id=request.company_id,
            period=request.period,
            metrics=request.metrics or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실적 검증 실패: {str(e)}")


@router.post("/tracking/calculate")
async def run_stock_tracking_agent(
    request: StockTrackingRequest,
    db: Session = Depends(get_db)
):
    """추천종목 추적 에이전트 실행"""
    try:
        agent = StockTrackingAgent(db)
        result = await agent.track_stock(
            recommendation_id=request.recommendation_id,
            tracking_period=request.tracking_period,
            benchmark_id=request.benchmark_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 추적 실패: {str(e)}")


@router.post("/orchestrator/run")
async def run_orchestrator_agent(
    request: OrchestratorRequest,
    db: Session = Depends(get_db)
):
    """멀티 LLM 오케스트레이터 실행"""
    try:
        agent = OrchestratorAgent(db)
        result = await agent.run(
            task=request.task,
            context=request.context or {},
            params=request.params or {},
            quality_threshold=request.quality_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오케스트레이터 실행 실패: {str(e)}")


@router.post("/portfolio/analyze")
async def run_portfolio_analysis_agent(
    request: PortfolioAnalysisRequest,
    db: Session = Depends(get_db)
):
    """포트폴리오 분석 에이전트 실행"""
    try:
        agent = PortfolioAnalysisAgent(db)
        result = await agent.analyze_portfolio(
            portfolio_id=request.portfolio_id,
            holdings=request.holdings,
            constraints=request.constraints or {},
            target_return=request.target_return
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"포트폴리오 분석 실패: {str(e)}")


@router.get("/status")
async def get_agents_status(db: Session = Depends(get_db)):
    """에이전트 상태 조회 - 실제 데이터 기반"""
    from app.models.collection_job import CollectionJob
    from app.models.evaluation import Evaluation
    from app.models.report import Report
    from app.models.data_collection_log import DataCollectionLog
    from app.models.enums import CollectionJobStatus, EvaluationStatus, ReportStatus
    from datetime import datetime, timedelta
    
    # 최근 24시간 내 실행된 작업으로 에이전트 상태 판단
    recent_time = datetime.utcnow() - timedelta(hours=24)
    
    agents_info = []
    
    # 각 에이전트별 최근 작업 상태 확인
    agent_configs = [
        ("evaluation", "평가 에이전트", Evaluation, EvaluationStatus),
        ("data_collection", "데이터 수집 에이전트", CollectionJob, CollectionJobStatus),
        ("report_parsing", "리포트 파싱 에이전트", Report, ReportStatus),
        ("award", "어워드 에이전트", None, None),
        ("report_generation", "리포트 생성 에이전트", None, None),
        ("company_verification", "기업정보 검증 에이전트", None, None),
        ("performance_verification", "실적 검증 에이전트", None, None),
        ("stock_tracking", "추천종목 추적 에이전트", None, None),
        ("orchestrator", "멀티 LLM 오케스트레이터", None, None),
        ("portfolio_analysis", "포트폴리오 분석 에이전트", None, None),
    ]
    
    for agent_name, description, model_class, status_enum in agent_configs:
        status = "inactive"
        last_run = None
        
        if model_class == Evaluation:
            # 평가 에이전트: 최근 평가 작업 확인
            recent_item = db.query(Evaluation).filter(
                Evaluation.created_at >= recent_time
            ).order_by(Evaluation.created_at.desc()).first()
            
            if recent_item:
                if recent_item.status == EvaluationStatus.COMPLETED.value:
                    status = "active"
                elif recent_item.status == EvaluationStatus.PROCESSING.value:
                    status = "running"
                elif recent_item.status == EvaluationStatus.FAILED.value:
                    status = "error"
                last_run = recent_item.created_at.isoformat()
        
        elif model_class == CollectionJob:
            # 데이터 수집 에이전트: 최근 수집 작업 확인
            recent_item = db.query(CollectionJob).filter(
                CollectionJob.created_at >= recent_time
            ).order_by(CollectionJob.created_at.desc()).first()
            
            if recent_item:
                if recent_item.status == CollectionJobStatus.COMPLETED.value:
                    status = "active"
                elif recent_item.status == CollectionJobStatus.RUNNING.value:
                    status = "running"
                elif recent_item.status == CollectionJobStatus.FAILED.value:
                    status = "error"
                last_run = recent_item.created_at.isoformat()
        
        elif model_class == Report:
            # 리포트 파싱 에이전트: 최근 리포트 파싱 확인
            recent_item = db.query(Report).filter(
                Report.created_at >= recent_time,
                Report.status.in_([ReportStatus.PROCESSING.value, ReportStatus.COMPLETED.value])
            ).order_by(Report.created_at.desc()).first()
            
            if recent_item:
                if recent_item.status == ReportStatus.COMPLETED.value:
                    status = "active"
                elif recent_item.status == ReportStatus.PROCESSING.value:
                    status = "running"
                last_run = recent_item.created_at.isoformat()
        
        else:
            # 기타 에이전트: 데이터 수집 로그에서 확인
            recent_log = db.query(DataCollectionLog).filter(
                DataCollectionLog.collection_type.like(f"%{agent_name}%"),
                DataCollectionLog.created_at >= recent_time
            ).order_by(DataCollectionLog.created_at.desc()).first()
            
            if recent_log:
                if recent_log.status == "success":
                    status = "active"
                elif recent_log.status == "failed":
                    status = "error"
                last_run = recent_log.created_at.isoformat()
        
        agents_info.append({
            "name": agent_name,
            "status": status,
            "description": description,
            "last_run": last_run
        })
    
    return {
        "agents": agents_info,
        "total": len(agents_info),
        "active_count": sum(1 for a in agents_info if a["status"] == "active"),
        "timestamp": datetime.utcnow().isoformat()
    }


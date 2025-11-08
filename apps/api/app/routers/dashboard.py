"""
Dashboard router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.dashboard import (
    DashboardStatsResponse,
    RecentEvaluationsResponse,
    RecentEvaluationItem,
    AwardStatusResponse,
    AwardStatusItem
)
from app.models.report import Report
from app.models.evaluation import Evaluation
from app.models.award import Award
from app.models.analyst import Analyst

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """대시보드 통계"""
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    total_evaluations = db.query(func.count(Evaluation.id)).scalar() or 0
    total_awards = db.query(func.count(Award.id)).scalar() or 0
    total_analysts = db.query(func.count(Analyst.id)).scalar() or 0
    
    # 최근 7일 평가
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_evaluations_count = db.query(func.count(Evaluation.id)).filter(
        Evaluation.created_at >= seven_days_ago
    ).scalar() or 0
    
    # 대기 중인 평가
    pending_evaluations_count = db.query(func.count(Evaluation.id)).filter(
        Evaluation.status == "processing"
    ).scalar() or 0
    
    return DashboardStatsResponse(
        total_reports=total_reports,
        total_evaluations=total_evaluations,
        total_awards=total_awards,
        total_analysts=total_analysts,
        recent_evaluations_count=recent_evaluations_count,
        pending_evaluations_count=pending_evaluations_count
    )


@router.get("/recent-evaluations", response_model=RecentEvaluationsResponse)
async def get_recent_evaluations(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """최근 평가 조회"""
    from app.models.analyst import Analyst
    from app.models.company import Company
    
    evaluations = db.query(Evaluation).order_by(
        Evaluation.created_at.desc()
    ).limit(limit).all()
    
    items = []
    for eval in evaluations:
        analyst = db.query(Analyst).filter(Analyst.id == eval.analyst_id).first()
        company = None
        if eval.company_id:
            company = db.query(Company).filter(Company.id == eval.company_id).first()
        
        items.append(RecentEvaluationItem(
            id=str(eval.id),
            analyst_name=analyst.name if analyst else "Unknown",
            company_name=company.name_kr if company else None,
            final_score=float(eval.final_score) if eval.final_score else None,
            status=eval.status,
            created_at=eval.created_at
        ))
    
    return RecentEvaluationsResponse(
        evaluations=items,
        total=len(items)
    )


@router.get("/award-status", response_model=AwardStatusResponse)
async def get_award_status(
    period: str = None,
    db: Session = Depends(get_db)
):
    """어워즈 현황"""
    
    if not period:
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        period = f"{now.year}-Q{quarter}"
    
    awards = db.query(Award).filter(
        Award.period.like(f"{period}%")
    ).all()
    
    # 카테고리별 집계
    category_stats: dict = {}
    for award in awards:
        category = award.award_category or "전체"
        if category not in category_stats:
            category_stats[category] = {"gold": 0, "silver": 0, "bronze": 0}
        
        if award.award_type == "gold":
            category_stats[category]["gold"] += 1
        elif award.award_type == "silver":
            category_stats[category]["silver"] += 1
        elif award.award_type == "bronze":
            category_stats[category]["bronze"] += 1
    
    awards_by_category = [
        AwardStatusItem(
            category=category,
            gold_count=stats["gold"],
            silver_count=stats["silver"],
            bronze_count=stats["bronze"],
            total=stats["gold"] + stats["silver"] + stats["bronze"]
        )
        for category, stats in category_stats.items()
    ]
    
    return AwardStatusResponse(
        awards_by_category=awards_by_category,
        total_awards=len(awards),
        period=period
    )


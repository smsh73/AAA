"""
Dashboard schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DashboardStatsResponse(BaseModel):
    total_reports: int
    total_evaluations: int
    total_awards: int
    total_analysts: int
    recent_evaluations_count: int
    pending_evaluations_count: int


class RecentEvaluationItem(BaseModel):
    id: str
    analyst_name: str
    company_name: Optional[str] = None
    final_score: Optional[float] = None
    status: str
    created_at: datetime


class RecentEvaluationsResponse(BaseModel):
    evaluations: List[RecentEvaluationItem]
    total: int


class AwardStatusItem(BaseModel):
    category: str
    gold_count: int
    silver_count: int
    bronze_count: int
    total: int


class AwardStatusResponse(BaseModel):
    awards_by_category: List[AwardStatusItem]
    total_awards: int
    period: str


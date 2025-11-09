"""
Enum 정의
"""
from enum import Enum


class EvaluationStatus(str, Enum):
    """평가 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportStatus(str, Enum):
    """리포트 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CollectionJobStatus(str, Enum):
    """데이터 수집 작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


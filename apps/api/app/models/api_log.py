"""
API Log model - 모든 API 호출 로그 기록
"""
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime


class ApiLog(BaseModel):
    """API 호출 로그 모델"""
    __tablename__ = "api_logs"

    # 요청 정보
    method = Column(String(10), nullable=False, index=True)  # GET, POST, PUT, DELETE 등
    path = Column(String(500), nullable=False, index=True)  # API 경로
    endpoint = Column(String(500))  # 전체 엔드포인트
    query_params = Column(JSONB)  # 쿼리 파라미터
    path_params = Column(JSONB)  # 경로 파라미터
    request_body = Column(JSONB)  # 요청 본문 (민감 정보 제외)
    request_headers = Column(JSONB)  # 요청 헤더 (민감 정보 제외)
    
    # 응답 정보
    status_code = Column(Integer, nullable=False, index=True)  # HTTP 상태 코드
    response_body = Column(JSONB)  # 응답 본문 (큰 응답은 요약)
    response_size = Column(Integer)  # 응답 크기 (bytes)
    
    # 사용자 정보
    user_id = Column(String(255), index=True)  # 사용자 ID (세션/토큰에서 추출)
    user_agent = Column(String(500))  # User-Agent
    client_ip = Column(String(50), index=True)  # 클라이언트 IP
    
    # 성능 정보
    request_time = Column(Float)  # 요청 처리 시간 (초)
    db_query_count = Column(Integer)  # DB 쿼리 횟수
    db_query_time = Column(Float)  # DB 쿼리 총 시간 (초)
    
    # 에러 정보
    error_code = Column(String(50), index=True)  # 에러 코드
    error_message = Column(Text)  # 에러 메시지
    error_traceback = Column(Text)  # 에러 스택 트레이스
    error_type = Column(String(100))  # 에러 타입 (Exception 클래스명)
    
    # 함수 호출 정보
    function_calls = Column(JSONB)  # 호출된 함수 목록 및 정보
    service_calls = Column(JSONB)  # 호출된 서비스 목록
    external_api_calls = Column(JSONB)  # 외부 API 호출 정보
    
    # 디버깅 정보
    debug_info = Column(JSONB)  # 디버깅을 위한 추가 정보
    feedback_loop = Column(JSONB)  # 피드백 루프 정보
    improvement_suggestions = Column(JSONB)  # 개선 제안
    
    # 메타데이터
    request_id = Column(String(100), index=True)  # 요청 추적 ID
    correlation_id = Column(String(100), index=True)  # 상관관계 ID
    session_id = Column(String(100), index=True)  # 세션 ID
    
    # 인덱스 추가
    __table_args__ = (
        Index('idx_api_logs_created_at', 'created_at'),
        Index('idx_api_logs_user_created', 'user_id', 'created_at'),
        Index('idx_api_logs_path_method', 'path', 'method'),
        Index('idx_api_logs_status_code', 'status_code', 'created_at'),
    )


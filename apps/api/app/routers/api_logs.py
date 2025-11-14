"""
API Logs router - 로그 관리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
import json
import csv
from io import StringIO

from app.database import get_db
from app.models.api_log import ApiLog

router = APIRouter()


@router.get("/logs")
async def get_api_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    client_ip: Optional[str] = Query(None),
    error_only: bool = Query(False),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db)
):
    """API 로그 조회 (성능 최적화)"""
    from datetime import datetime as dt
    
    query = db.query(ApiLog)
    
    # 필터링 (인덱스 활용)
    if method:
        query = query.filter(ApiLog.method == method.upper())
    if path:
        query = query.filter(ApiLog.path.ilike(f"%{path}%"))
    if status_code:
        query = query.filter(ApiLog.status_code == status_code)
    if user_id:
        query = query.filter(ApiLog.user_id == user_id)
    if client_ip:
        query = query.filter(ApiLog.client_ip == client_ip)
    if error_only:
        query = query.filter(ApiLog.status_code >= 400)
    
    # 날짜 필터링 (파싱 개선)
    if start_date:
        try:
            if 'T' in start_date:
                parsed_start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                parsed_start = dt.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ApiLog.created_at >= parsed_start)
        except (ValueError, AttributeError):
            pass
    
    if end_date:
        try:
            if 'T' in end_date:
                parsed_end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                parsed_end = dt.strptime(end_date, "%Y-%m-%d")
                parsed_end = parsed_end.replace(hour=23, minute=59, second=59)
            query = query.filter(ApiLog.created_at <= parsed_end)
        except (ValueError, AttributeError):
            pass
    
    # 정렬 및 페이징 (인덱스 활용 - created_at 인덱스 사용)
    # count 쿼리 최적화: 필터 적용 후 count
    total = query.count()
    # 데이터 조회: 인덱스 활용하여 빠르게 조회
    logs = query.order_by(ApiLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": str(log.id),
                "method": log.method,
                "path": log.path,
                "endpoint": log.endpoint,
                "status_code": log.status_code,
                "user_id": log.user_id,
                "client_ip": log.client_ip,
                "request_time": log.request_time,
                "error_code": log.error_code,
                "error_message": log.error_message,
                "error_type": log.error_type,
                "function_calls": log.function_calls,
                "service_calls": log.service_calls,
                "external_api_calls": log.external_api_calls,
                "request_id": log.request_id,
                "session_id": log.session_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@router.get("/logs/{log_id}")
async def get_api_log_detail(
    log_id: UUID,
    db: Session = Depends(get_db)
):
    """API 로그 상세 조회"""
    log = db.query(ApiLog).filter(ApiLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {
        "id": str(log.id),
        "method": log.method,
        "path": log.path,
        "endpoint": log.endpoint,
        "query_params": log.query_params,
        "path_params": log.path_params,
        "request_body": log.request_body,
        "request_headers": log.request_headers,
        "status_code": log.status_code,
        "response_body": log.response_body,
        "response_size": log.response_size,
        "user_id": log.user_id,
        "user_agent": log.user_agent,
        "client_ip": log.client_ip,
        "request_time": log.request_time,
        "db_query_count": log.db_query_count,
        "db_query_time": log.db_query_time,
        "error_code": log.error_code,
        "error_message": log.error_message,
        "error_traceback": log.error_traceback,
        "error_type": log.error_type,
        "function_calls": log.function_calls,
        "service_calls": log.service_calls,
        "external_api_calls": log.external_api_calls,
        "debug_info": log.debug_info,
        "feedback_loop": log.feedback_loop,
        "improvement_suggestions": log.improvement_suggestions,
        "request_id": log.request_id,
        "correlation_id": log.correlation_id,
        "session_id": log.session_id,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "updated_at": log.updated_at.isoformat() if log.updated_at else None,
    }


@router.get("/logs/download/json")
async def download_logs_json(
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    error_only: bool = Query(False),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """로그를 JSON 형식으로 다운로드"""
    from datetime import datetime as dt
    
    query = db.query(ApiLog)
    
    # 필터링
    if method:
        query = query.filter(ApiLog.method == method.upper())
    if path:
        query = query.filter(ApiLog.path.ilike(f"%{path}%"))
    if status_code:
        query = query.filter(ApiLog.status_code == status_code)
    if user_id:
        query = query.filter(ApiLog.user_id == user_id)
    if error_only:
        query = query.filter(ApiLog.status_code >= 400)
    
    # 날짜 필터링 (파싱 개선)
    if start_date:
        try:
            if 'T' in start_date:
                parsed_start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                parsed_start = dt.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ApiLog.created_at >= parsed_start)
        except (ValueError, AttributeError):
            pass
    
    if end_date:
        try:
            if 'T' in end_date:
                parsed_end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                parsed_end = dt.strptime(end_date, "%Y-%m-%d")
                parsed_end = parsed_end.replace(hour=23, minute=59, second=59)
            query = query.filter(ApiLog.created_at <= parsed_end)
        except (ValueError, AttributeError):
            pass
    
    logs = query.order_by(ApiLog.created_at.desc()).limit(limit).all()
    
    # JSON 변환
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": str(log.id),
            "method": log.method,
            "path": log.path,
            "endpoint": log.endpoint,
            "query_params": log.query_params,
            "path_params": log.path_params,
            "request_body": log.request_body,
            "request_headers": log.request_headers,
            "status_code": log.status_code,
            "response_body": log.response_body,
            "response_size": log.response_size,
            "user_id": log.user_id,
            "user_agent": log.user_agent,
            "client_ip": log.client_ip,
            "request_time": log.request_time,
            "db_query_count": log.db_query_count,
            "db_query_time": log.db_query_time,
            "error_code": log.error_code,
            "error_message": log.error_message,
            "error_traceback": log.error_traceback,
            "error_type": log.error_type,
            "function_calls": log.function_calls,
            "service_calls": log.service_calls,
            "external_api_calls": log.external_api_calls,
            "debug_info": log.debug_info,
            "feedback_loop": log.feedback_loop,
            "improvement_suggestions": log.improvement_suggestions,
            "request_id": log.request_id,
            "correlation_id": log.correlation_id,
            "session_id": log.session_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        })
    
    json_str = json.dumps(logs_data, indent=2, ensure_ascii=False, default=str)
    
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=api_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


@router.get("/logs/download/csv")
async def download_logs_csv(
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    error_only: bool = Query(False),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """로그를 CSV 형식으로 다운로드"""
    from datetime import datetime as dt
    
    query = db.query(ApiLog)
    
    # 필터링
    if method:
        query = query.filter(ApiLog.method == method.upper())
    if path:
        query = query.filter(ApiLog.path.ilike(f"%{path}%"))
    if status_code:
        query = query.filter(ApiLog.status_code == status_code)
    if user_id:
        query = query.filter(ApiLog.user_id == user_id)
    if error_only:
        query = query.filter(ApiLog.status_code >= 400)
    
    # 날짜 필터링 (파싱 개선)
    if start_date:
        try:
            if 'T' in start_date:
                parsed_start = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                parsed_start = dt.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ApiLog.created_at >= parsed_start)
        except (ValueError, AttributeError):
            pass
    
    if end_date:
        try:
            if 'T' in end_date:
                parsed_end = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                parsed_end = dt.strptime(end_date, "%Y-%m-%d")
                parsed_end = parsed_end.replace(hour=23, minute=59, second=59)
            query = query.filter(ApiLog.created_at <= parsed_end)
        except (ValueError, AttributeError):
            pass
    
    logs = query.order_by(ApiLog.created_at.desc()).limit(limit).all()
    
    # CSV 변환
    output = StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow([
        "ID", "Method", "Path", "Status Code", "User ID", "Client IP",
        "Request Time", "Error Code", "Error Message", "Error Type",
        "Function Calls", "Service Calls", "External API Calls",
        "Request ID", "Session ID", "Created At"
    ])
    
    # 데이터
    for log in logs:
        writer.writerow([
            str(log.id),
            log.method,
            log.path,
            log.status_code,
            log.user_id or "",
            log.client_ip or "",
            log.request_time or "",
            log.error_code or "",
            (log.error_message or "")[:200],  # 최대 200자
            log.error_type or "",
            json.dumps(log.function_calls) if log.function_calls else "",
            json.dumps(log.service_calls) if log.service_calls else "",
            json.dumps(log.external_api_calls) if log.external_api_calls else "",
            log.request_id or "",
            log.session_id or "",
            log.created_at.isoformat() if log.created_at else "",
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=api_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/logs/stats")
async def get_log_stats(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db)
):
    """로그 통계 조회"""
    from datetime import datetime as dt
    
    query = db.query(ApiLog)
    
    # 날짜 파라미터 파싱
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            # ISO 형식 또는 날짜 형식 파싱
            if 'T' in start_date:
                parsed_start_date = dt.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                parsed_start_date = dt.strptime(start_date, "%Y-%m-%d")
        except (ValueError, AttributeError):
            # 파싱 실패 시 무시
            pass
    
    if end_date:
        try:
            if 'T' in end_date:
                parsed_end_date = dt.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                parsed_end_date = dt.strptime(end_date, "%Y-%m-%d")
                # 날짜만 제공된 경우 하루 끝 시간으로 설정
                parsed_end_date = parsed_end_date.replace(hour=23, minute=59, second=59)
        except (ValueError, AttributeError):
            pass
    
    if parsed_start_date:
        query = query.filter(ApiLog.created_at >= parsed_start_date)
    if parsed_end_date:
        query = query.filter(ApiLog.created_at <= parsed_end_date)
    
    # 통계 계산 (쿼리 최적화)
    total = query.count()
    errors = query.filter(ApiLog.status_code >= 400).count()
    success = total - errors
    
    # 평균 응답 시간 (필터 적용)
    avg_time_query = db.query(func.avg(ApiLog.request_time)).filter(
        ApiLog.request_time.isnot(None)
    )
    if parsed_start_date:
        avg_time_query = avg_time_query.filter(ApiLog.created_at >= parsed_start_date)
    if parsed_end_date:
        avg_time_query = avg_time_query.filter(ApiLog.created_at <= parsed_end_date)
    avg_time = avg_time_query.scalar() or 0.0
    
    # 상태 코드별 통계 (필터 적용)
    status_query = db.query(
        ApiLog.status_code,
        func.count(ApiLog.id).label('count')
    )
    if parsed_start_date:
        status_query = status_query.filter(ApiLog.created_at >= parsed_start_date)
    if parsed_end_date:
        status_query = status_query.filter(ApiLog.created_at <= parsed_end_date)
    status_stats = status_query.group_by(ApiLog.status_code).all()
    
    # 메서드별 통계 (필터 적용)
    method_query = db.query(
        ApiLog.method,
        func.count(ApiLog.id).label('count')
    )
    if parsed_start_date:
        method_query = method_query.filter(ApiLog.created_at >= parsed_start_date)
    if parsed_end_date:
        method_query = method_query.filter(ApiLog.created_at <= parsed_end_date)
    method_stats = method_query.group_by(ApiLog.method).all()
    
    # 경로별 통계 (상위 10개, 필터 적용)
    path_query = db.query(
        ApiLog.path,
        func.count(ApiLog.id).label('count')
    )
    if parsed_start_date:
        path_query = path_query.filter(ApiLog.created_at >= parsed_start_date)
    if parsed_end_date:
        path_query = path_query.filter(ApiLog.created_at <= parsed_end_date)
    path_stats = path_query.group_by(ApiLog.path).order_by(func.count(ApiLog.id).desc()).limit(10).all()
    
    return {
        "total": total,
        "success": success,
        "errors": errors,
        "error_rate": round((errors / total * 100) if total > 0 else 0.0, 2),
        "avg_request_time": round(float(avg_time), 4),
        "status_code_stats": [{"status_code": s[0], "count": s[1]} for s in status_stats],
        "method_stats": [{"method": m[0], "count": m[1]} for m in method_stats],
        "top_paths": [{"path": p[0], "count": p[1]} for p in path_stats],
    }


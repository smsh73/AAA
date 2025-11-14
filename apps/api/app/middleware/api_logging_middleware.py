"""
API Logging Middleware - 모든 API 호출 로깅
"""
import time
import json
import traceback
import inspect
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import uuid4
import sys

from app.database import SessionLocal
from app.models.api_log import ApiLog


class ApiLoggingMiddleware(BaseHTTPMiddleware):
    """API 호출 로깅 미들웨어"""

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 제외 경로 체크
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 요청 시작 시간
        start_time = time.time()
        request_id = str(uuid4())
        
        # 요청 정보 수집
        method = request.method
        path = request.url.path
        endpoint = str(request.url)
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # 요청 본문 읽기 (한 번만)
        request_body = None
        try:
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    try:
                        request_body = json.loads(body.decode())
                        # 민감 정보 제거
                        request_body = self._sanitize_data(request_body)
                    except:
                        request_body = {"raw": body.decode()[:1000]}  # 최대 1000자
        except Exception as e:
            request_body = {"error": str(e)}

        # 요청 헤더 수집 (민감 정보 제외)
        request_headers = dict(request.headers)
        request_headers = self._sanitize_headers(request_headers)

        # 함수 호출 추적 설정
        function_calls = []
        service_calls = []
        external_api_calls = []
        db_query_count = 0
        db_query_time = 0.0

        # 응답 처리
        status_code = 500
        response_body = None
        response_size = 0
        error_code = None
        error_message = None
        error_traceback = None
        error_type = None

        try:
            # 응답 생성
            response = await call_next(request)
            status_code = response.status_code

            # 응답 본문 읽기
            if hasattr(response, 'body'):
                try:
                    response_body = json.loads(response.body.decode())
                    response_size = len(response.body)
                    # 큰 응답은 요약
                    if response_size > 10000:
                        response_body = {
                            "summary": "Response too large",
                            "size": response_size,
                            "preview": str(response_body)[:500]
                        }
                except:
                    pass
            elif isinstance(response, StreamingResponse):
                response_size = -1  # 스트리밍 응답

        except Exception as e:
            # 에러 발생 시
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            error_code = self._get_error_code(e)
            
            # 에러 응답 생성
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": error_message}
            )

        # 요청 처리 시간
        request_time = time.time() - start_time

        # 로그 저장 (비동기로 처리하여 응답 지연 최소화)
        try:
            self._save_log_async(
                method=method,
                path=path,
                endpoint=endpoint,
                query_params=query_params,
                path_params={},  # 경로 파라미터는 라우터에서 추출 필요
                request_body=request_body,
                request_headers=request_headers,
                status_code=status_code,
                response_body=response_body,
                response_size=response_size,
                user_id=self._extract_user_id(request),
                user_agent=user_agent,
                client_ip=client_ip,
                request_time=request_time,
                db_query_count=db_query_count,
                db_query_time=db_query_time,
                error_code=error_code,
                error_message=error_message,
                error_traceback=error_traceback,
                error_type=error_type,
                function_calls=function_calls,
                service_calls=service_calls,
                external_api_calls=external_api_calls,
                request_id=request_id,
                session_id=self._extract_session_id(request)
            )
        except Exception as e:
            # 로그 저장 실패해도 응답은 정상 처리
            print(f"API 로그 저장 실패: {str(e)}")

        return response

    def _save_log_async(
        self,
        method: str,
        path: str,
        endpoint: str,
        query_params: dict,
        path_params: dict,
        request_body: dict,
        request_headers: dict,
        status_code: int,
        response_body: dict,
        response_size: int,
        user_id: str,
        user_agent: str,
        client_ip: str,
        request_time: float,
        db_query_count: int,
        db_query_time: float,
        error_code: str,
        error_message: str,
        error_traceback: str,
        error_type: str,
        function_calls: list,
        service_calls: list,
        external_api_calls: list,
        request_id: str,
        session_id: str
    ):
        """로그를 데이터베이스에 저장"""
        db = SessionLocal()
        try:
            log = ApiLog(
                method=method,
                path=path,
                endpoint=endpoint,
                query_params=query_params,
                path_params=path_params,
                request_body=request_body,
                request_headers=request_headers,
                status_code=status_code,
                response_body=response_body,
                response_size=response_size,
                user_id=user_id,
                user_agent=user_agent,
                client_ip=client_ip,
                request_time=request_time,
                db_query_count=db_query_count,
                db_query_time=db_query_time,
                error_code=error_code,
                error_message=error_message,
                error_traceback=error_traceback,
                error_type=error_type,
                function_calls=function_calls,
                service_calls=service_calls,
                external_api_calls=external_api_calls,
                request_id=request_id,
                session_id=session_id,
                debug_info={
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"API 로그 저장 오류: {str(e)}")
        finally:
            db.close()

    def _sanitize_data(self, data: dict) -> dict:
        """민감 정보 제거"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = ["password", "token", "api_key", "secret", "authorization", "cookie"]
        sanitized = {}
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_headers(self, headers: dict) -> dict:
        """헤더에서 민감 정보 제거"""
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        sanitized = {}
        for key, value in headers.items():
            if any(sh in key.lower() for sh in sensitive_headers):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _extract_user_id(self, request: Request) -> str:
        """요청에서 사용자 ID 추출"""
        # 헤더에서 추출 시도
        user_id = request.headers.get("x-user-id")
        if user_id:
            return user_id
        
        # 쿠키에서 추출 시도
        session = request.cookies.get("session")
        if session:
            # 세션에서 사용자 ID 추출 로직 (실제 구현 필요)
            return f"session:{session[:8]}"
        
        # 기본값
        return "anonymous"

    def _extract_session_id(self, request: Request) -> str:
        """세션 ID 추출"""
        return request.cookies.get("session_id") or request.headers.get("x-session-id") or ""

    def _get_error_code(self, error: Exception) -> str:
        """에러 코드 추출"""
        error_type = type(error).__name__
        if hasattr(error, 'status_code'):
            return f"{error_type}_{error.status_code}"
        return error_type


"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from app.middleware.api_logging_middleware import ApiLoggingMiddleware

from app.routers import (
    analysts,
    reports,
    companies,
    evaluations,
    scorecards,
    scores,
    awards,
    data_collection,
    evaluation_reports,
    agents,
    health,
    dashboard,
    api_logs,
)

app = FastAPI(
    title="AI가 찾은 스타 애널리스트 어워즈 API",
    description="멀티 LLM 기반 애널리스트 평가 시스템",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 로깅 미들웨어 (CORS 이후에 추가)
app.add_middleware(ApiLoggingMiddleware)

# 라우터 등록
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(analysts.router, prefix="/api/analysts", tags=["Analysts"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(scorecards.router, prefix="/api/scorecards", tags=["Scorecards"])
app.include_router(scores.router, prefix="/api/scores", tags=["Scores"])
app.include_router(awards.router, prefix="/api/awards", tags=["Awards"])
app.include_router(data_collection.router, prefix="/api/data-collection", tags=["Data Collection"])
app.include_router(evaluation_reports.router, prefix="/api/evaluation-reports", tags=["Evaluation Reports"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(api_logs.router, prefix="/api", tags=["API Logs"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# 애플리케이션 시작 시 자동 마이그레이션 (환경 변수로 제어)
if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
    from app.database import run_migrations
    run_migrations()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


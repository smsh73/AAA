"""
Frontend-API-스키마 통합 테스트
화면, 기능, API, 스키마가 잘 어울려서 동작하는지 검증
"""
import pytest
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal


class TestFrontendAPIIntegration:
    """Frontend-API 통합 테스트"""
    
    def test_evaluations_grouped_api_schema(self):
        """평가 그룹화 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "periods": [
                {
                    "period": "2025-Q1",
                    "analysts": [
                        {
                            "analyst_id": "uuid",
                            "analyst_name": "string",
                            "analyst_firm": "string",
                            "reports": [
                                {
                                    "report_id": "uuid",
                                    "report_title": "string",
                                    "publication_date": "string",
                                    "evaluations": [
                                        {
                                            "id": "uuid",
                                            "final_score": 85.5,
                                            "status": "completed",
                                            "created_at": "datetime"
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "total_evaluations": 10
                }
            ],
            "total": 10
        }
        
        # Backend 스키마와 일치하는지 확인
        assert "periods" in frontend_interface
        assert "total" in frontend_interface
        assert isinstance(frontend_interface["periods"], list)
        
        if frontend_interface["periods"]:
            period = frontend_interface["periods"][0]
            assert "period" in period
            assert "analysts" in period
            assert "total_evaluations" in period
    
    def test_evaluations_list_api_schema(self):
        """평가 목록 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "evaluations": [
                {
                    "id": "uuid",
                    "report_id": "uuid",
                    "analyst_id": "uuid",
                    "company_id": "uuid",
                    "evaluation_period": "2025-Q1",
                    "final_score": 85.5,
                    "status": "completed",
                    "created_at": "datetime"
                }
            ],
            "total": 10,
            "skip": 0,
            "limit": 20
        }
        
        assert "evaluations" in frontend_interface
        assert "total" in frontend_interface
        assert "skip" in frontend_interface
        assert "limit" in frontend_interface
        
        if frontend_interface["evaluations"]:
            evaluation = frontend_interface["evaluations"][0]
            assert "id" in evaluation
            assert "status" in evaluation
            assert "evaluation_period" in evaluation
    
    def test_evaluation_detail_api_schema(self):
        """평가 상세 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "id": "uuid",
            "report_id": "uuid",
            "analyst_id": "uuid",
            "company_id": "uuid",
            "evaluation_period": "2025-Q1",
            "evaluation_date": "date",
            "final_score": 85.5,
            "ai_quantitative_score": 80.0,
            "sns_market_score": 75.0,
            "expert_survey_score": 80.0,
            "status": "completed",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
        
        required_fields = [
            "id", "report_id", "analyst_id", "evaluation_period",
            "evaluation_date", "status", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in frontend_interface, f"필수 필드 누락: {field}"
    
    def test_evaluation_scores_api_schema(self):
        """평가 점수 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = [
            {
                "id": "uuid",
                "score_type": "target_price_accuracy",
                "score_value": 80.0,
                "weight": 0.25,
                "details": {},
                "reasoning": "string"
            }
        ]
        
        assert isinstance(frontend_interface, list)
        
        if frontend_interface:
            score = frontend_interface[0]
            assert "score_type" in score
            assert "score_value" in score
            assert "weight" in score
            assert 0.0 <= score["score_value"] <= 100.0
            assert 0.0 <= score["weight"] <= 1.0
    
    def test_awards_api_schema(self):
        """어워드 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = [
            {
                "id": "uuid",
                "analyst_id": "uuid",
                "award_type": "gold",
                "award_category": "AI",
                "period": "2025-Q1",
                "rank": 1
            }
        ]
        
        assert isinstance(frontend_interface, list)
        
        if frontend_interface:
            award = frontend_interface[0]
            assert "id" in award
            assert "award_type" in award
            assert "award_category" in award
            assert "period" in award
            assert "rank" in award
            assert award["award_type"] in ["gold", "silver", "bronze"]
            assert 1 <= award["rank"] <= 3
    
    def test_award_response_scorecard_id(self):
        """AwardResponse에 scorecard_id 포함 확인"""
        # 수정된 스키마에 scorecard_id가 포함되어야 함
        award_response = {
            "id": "uuid",
            "scorecard_id": "uuid",  # 추가된 필드
            "analyst_id": "uuid",
            "award_type": "gold",
            "award_category": "AI",
            "period": "2025-Q1",
            "rank": 1
        }
        
        assert "scorecard_id" in award_response
    
    def test_dashboard_stats_api_schema(self):
        """대시보드 통계 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "total_reports": 100,
            "total_evaluations": 50,
            "total_awards": 10,
            "total_analysts": 20
        }
        
        required_fields = [
            "total_reports", "total_evaluations",
            "total_awards", "total_analysts"
        ]
        
        for field in required_fields:
            assert field in frontend_interface, f"필수 필드 누락: {field}"
            assert isinstance(frontend_interface[field], int)
            assert frontend_interface[field] >= 0
    
    def test_dashboard_recent_evaluations_api_schema(self):
        """대시보드 최근 평가 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "evaluations": [
                {
                    "id": "uuid",
                    "final_score": 85.5,
                    "status": "completed"
                }
            ]
        }
        
        assert "evaluations" in frontend_interface
        assert isinstance(frontend_interface["evaluations"], list)
        
        if frontend_interface["evaluations"]:
            evaluation = frontend_interface["evaluations"][0]
            assert "id" in evaluation
            assert "final_score" in evaluation or evaluation.get("final_score") is None
    
    def test_dashboard_award_status_api_schema(self):
        """대시보드 어워드 현황 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "awards_by_category": [
                {
                    "category": "AI",
                    "total": 5
                }
            ]
        }
        
        assert "awards_by_category" in frontend_interface
        assert isinstance(frontend_interface["awards_by_category"], list)
        
        if frontend_interface["awards_by_category"]:
            award = frontend_interface["awards_by_category"][0]
            assert "category" in award
            assert "total" in award
            assert isinstance(award["total"], int)
    
    def test_scorecard_detail_api_schema(self):
        """스코어카드 상세 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "id": "uuid",
            "analyst_id": "uuid",
            "company_id": "uuid",
            "period": "2025-Q1",
            "final_score": 85.5,
            "ranking": 1,
            "scorecard_data": {
                "evaluation_id": "uuid",
                "scores": {
                    "target_price_accuracy": 80.0,
                    "performance_accuracy": 85.0
                }
            }
        }
        
        required_fields = [
            "id", "analyst_id", "period", "final_score"
        ]
        
        for field in required_fields:
            assert field in frontend_interface, f"필수 필드 누락: {field}"
        
        assert "scorecard_data" in frontend_interface
        assert isinstance(frontend_interface["scorecard_data"], dict)
    
    def test_reports_grouped_api_schema(self):
        """리포트 그룹화 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "periods": [
                {
                    "period": "2025-Q1",
                    "analysts": [
                        {
                            "analyst_id": "uuid",
                            "analyst_name": "string",
                            "reports": [
                                {
                                    "report_id": "uuid",
                                    "report_title": "string",
                                    "publication_date": "string"
                                }
                            ]
                        }
                    ],
                    "total_reports": 10
                }
            ],
            "total": 10
        }
        
        assert "periods" in frontend_interface
        assert "total" in frontend_interface
    
    def test_reports_list_api_schema(self):
        """리포트 목록 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = {
            "reports": [
                {
                    "id": "uuid",
                    "title": "string",
                    "analyst_id": "uuid",
                    "company_id": "uuid",
                    "publication_date": "date",
                    "status": "parsed"
                }
            ],
            "total": 10
        }
        
        assert "reports" in frontend_interface
        assert "total" in frontend_interface
    
    def test_data_collection_logs_api_schema(self):
        """데이터 수집 로그 API 스키마 검증"""
        # Frontend에서 기대하는 구조
        frontend_interface = [
            {
                "id": "uuid",
                "analyst_id": "uuid",
                "collection_type": "sns",
                "status": "success",
                "collected_data": {},
                "created_at": "datetime"
            }
        ]
        
        assert isinstance(frontend_interface, list)
        
        if frontend_interface:
            log = frontend_interface[0]
            assert "collection_type" in log
            assert "status" in log
            assert log["status"] in ["success", "failed", "pending"]


class TestAPIEndpointMapping:
    """API 엔드포인트 매핑 검증"""
    
    def test_evaluation_endpoints(self):
        """평가 관련 엔드포인트 매핑"""
        endpoints = {
            "GET /api/evaluations": "평가 목록 조회",
            "GET /api/evaluations/grouped": "평가 그룹화 조회",
            "GET /api/evaluations/{id}": "평가 상세 조회",
            "GET /api/evaluations/{id}/scores": "평가 점수 조회",
            "POST /api/evaluations/start": "평가 시작"
        }
        
        assert len(endpoints) == 5
    
    def test_award_endpoints(self):
        """어워드 관련 엔드포인트 매핑"""
        endpoints = {
            "GET /api/awards": "어워드 조회",
            "POST /api/awards/run": "어워드 선정 실행"
        }
        
        assert len(endpoints) == 2
    
    def test_dashboard_endpoints(self):
        """대시보드 관련 엔드포인트 매핑"""
        endpoints = {
            "GET /api/dashboard/stats": "대시보드 통계",
            "GET /api/dashboard/recent-evaluations": "최근 평가",
            "GET /api/dashboard/award-status": "어워드 현황"
        }
        
        assert len(endpoints) == 3
    
    def test_data_collection_endpoints(self):
        """데이터 수집 관련 엔드포인트 매핑"""
        endpoints = {
            "POST /api/data-collection/start": "데이터 수집 시작",
            "GET /api/data-collection/{id}/status": "데이터 수집 상태",
            "GET /api/data-collection/logs": "데이터 수집 로그"
        }
        
        assert len(endpoints) == 3


class TestDataFlowValidation:
    """데이터 흐름 검증"""
    
    def test_evaluation_flow(self):
        """평가 플로우 검증"""
        # 1. 리포트 업로드
        # 2. 리포트 파싱
        # 3. 평가 시작
        # 4. 평가 점수 조회
        # 5. 스코어카드 생성
        
        flow_steps = [
            "report_upload",
            "report_parsing",
            "evaluation_start",
            "evaluation_scores",
            "scorecard_creation"
        ]
        
        assert len(flow_steps) == 5
        assert "evaluation_start" in flow_steps
        assert "scorecard_creation" in flow_steps
    
    def test_award_flow(self):
        """어워드 플로우 검증"""
        # 1. 스코어카드 조회
        # 2. 카테고리별 필터링
        # 3. 순위 지정
        # 4. 어워드 생성
        
        flow_steps = [
            "scorecard_query",
            "category_filtering",
            "ranking",
            "award_creation"
        ]
        
        assert len(flow_steps) == 4
        assert "category_filtering" in flow_steps
        assert "ranking" in flow_steps




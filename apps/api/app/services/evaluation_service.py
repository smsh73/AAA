"""
Evaluation service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from app.models.evaluation import Evaluation, EvaluationScore
from app.models.enums import EvaluationStatus
from app.models.report import Report
from app.schemas.evaluation import EvaluationResponse
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.services.ai_agents.data_collection_agent import DataCollectionAgent
from app.services.scorecard_service import ScorecardService
from app.models.data_collection_log import DataCollectionLog
from app.tasks.evaluation_tasks import evaluate_report_task


class EvaluationService:
    """평가 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluation_agent = EvaluationAgent(db)
        self.data_collection_agent = DataCollectionAgent(db)
        self.scorecard_service = ScorecardService(db)

    async def start_evaluation(self, report_id: UUID) -> EvaluationResponse:
        """평가 시작"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 중복 평가 방지 (활성 상태만 체크)
        existing = self.db.query(Evaluation).filter(
            Evaluation.report_id == report_id,
            Evaluation.status.in_([EvaluationStatus.PENDING.value, EvaluationStatus.PROCESSING.value])
        ).first()
        
        if existing:
            raise ValueError(f"이미 진행 중인 평가가 있습니다: {existing.id}")
        
        evaluation = Evaluation(
            report_id=report_id,
            analyst_id=report.analyst_id,
            company_id=report.company_id,
            evaluation_period=self._get_current_period(),
            evaluation_date=datetime.now().date(),
            status=EvaluationStatus.PROCESSING.value
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        # 비동기 평가 시작 (Celery 작업)
        evaluate_report_task.delay(str(evaluation.id), str(report_id))

        return EvaluationResponse(
            evaluation_id=evaluation.id,
            status="processing",
            estimated_completion_time=datetime.utcnow() + timedelta(hours=1)
        )

    async def complete_evaluation(
        self,
        evaluation_id: UUID
    ) -> Dict[str, Any]:
        """평가 완료 및 스코어카드 생성"""
        evaluation = self.db.query(Evaluation).filter(
            Evaluation.id == evaluation_id
        ).first()
        
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # 평가 점수 조회 (7개 KPI 점수)
        evaluation_scores = self.db.query(EvaluationScore).filter(
            EvaluationScore.evaluation_id == evaluation_id
        ).all()

        # KPI 점수 매핑 (7개 KPI 점수를 모두 포함)
        kpi_scores = {}
        for score in evaluation_scores:
            kpi_scores[score.score_type] = float(score.score_value)
        
        # 1단계: AI 정량 분석 점수 (40%) - KPI 점수 기반 계산
        ai_quantitative_score = self._calculate_ai_quantitative_score(evaluation_scores)

        # 2단계: SNS·시장 반응 점수 (30%)
        sns_market_score = await self._calculate_sns_market_score(evaluation)

        # 3단계: 전문가 평가 및 설문 점수 (30%)
        expert_survey_score = await self._calculate_expert_survey_score(evaluation)

        # 최종 점수 계산
        final_score = (
            ai_quantitative_score * Decimal("0.40") +
            sns_market_score * Decimal("0.30") +
            expert_survey_score * Decimal("0.30")
        )
        
        # 상위 3개 점수도 포함 (하위 호환성)
        kpi_scores["ai_quantitative_score"] = float(ai_quantitative_score)
        kpi_scores["sns_market_score"] = float(sns_market_score)
        kpi_scores["expert_survey_score"] = float(expert_survey_score)
        
        # 스코어카드 생성
        scorecard = self.scorecard_service.create_scorecard(
            evaluation_id=evaluation_id,
            analyst_id=evaluation.analyst_id,
            company_id=evaluation.company_id,
            period=evaluation.evaluation_period,
            final_score=float(final_score),
            scores=kpi_scores
        )

        evaluation.status = EvaluationStatus.COMPLETED.value
        self.db.commit()

        return {
            "evaluation_id": evaluation_id,
            "final_score": float(final_score),
            "ai_quantitative_score": float(ai_quantitative_score),
            "sns_market_score": float(sns_market_score),
            "expert_survey_score": float(expert_survey_score),
            "scorecard_id": scorecard.id,
        }

    def _calculate_ai_quantitative_score(
        self,
        scores: list
    ) -> Decimal:
        """AI 정량 분석 점수 계산"""
        # KPI별 가중 평균
        weights = {
            "target_price_accuracy": Decimal("0.25"),
            "performance_accuracy": Decimal("0.30"),
            "investment_logic_validity": Decimal("0.15"),
            "risk_analysis_appropriateness": Decimal("0.10"),
            "report_frequency": Decimal("0.05"),
        }
        
        total_score = Decimal("0")
        total_weight = Decimal("0")
        
        for score in scores:
            weight = weights.get(score.score_type, Decimal("0"))
            if weight > 0:
                total_score += score.score_value * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else Decimal("0")

    async def _calculate_sns_market_score(
        self,
        evaluation: Evaluation
    ) -> Decimal:
        """SNS·시장 반응 점수 계산 - 실제 데이터 기반"""
        from datetime import datetime, timedelta
        
        # 최근 3개월 데이터 조회
        three_months_ago = datetime.now() - timedelta(days=90)
        
        # SNS 데이터 조회
        sns_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == evaluation.analyst_id,
            DataCollectionLog.collection_type == "sns",
            DataCollectionLog.status == "success",
            DataCollectionLog.created_at >= three_months_ago
        ).all()
        
        # Media 데이터 조회
        media_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == evaluation.analyst_id,
            DataCollectionLog.collection_type == "media",
            DataCollectionLog.status == "success",
            DataCollectionLog.created_at >= three_months_ago
        ).all()
        
        # SNS 주목도 점수 계산
        sns_score = Decimal("0.0")
        if sns_logs:
            total_attention = Decimal("0.0")
            valid_logs = 0
            
            for log in sns_logs:
                if log.collected_data:
                    attention_score = log.collected_data.get("attention_score", 0)
                    if attention_score > 0:
                        total_attention += Decimal(str(attention_score))
                        valid_logs += 1
            
            if valid_logs > 0:
                avg_attention = total_attention / Decimal(str(valid_logs))
                # 정규화 (기준: 평균 주목도 100 = 100점)
                sns_score = min(Decimal("100.0"), (avg_attention / Decimal("100.0")) * Decimal("100.0"))
        else:
            # 데이터가 없으면 기본값
            sns_score = Decimal("50.0")
        
        # 미디어 언급 빈도 점수 계산
        media_score = Decimal("0.0")
        if media_logs:
            total_mentions = len(media_logs)
            months = Decimal("3.0")
            monthly_mentions = Decimal(str(total_mentions)) / months
            
            # 기준: 월 10회 언급 = 100점
            if monthly_mentions >= Decimal("10.0"):
                media_score = Decimal("100.0")
            elif monthly_mentions >= Decimal("7.0"):
                media_score = Decimal("80.0")
            elif monthly_mentions >= Decimal("5.0"):
                media_score = Decimal("60.0")
            elif monthly_mentions >= Decimal("3.0"):
                media_score = Decimal("40.0")
            elif monthly_mentions >= Decimal("1.0"):
                media_score = Decimal("20.0")
            else:
                media_score = Decimal("10.0")
        else:
            # 데이터가 없으면 기본값
            media_score = Decimal("50.0")
        
        # SNS 주목도 (10%) + 언론 빈도 (5%) = 15%
        # 전체 30% 중 15%이므로 가중 평균
        return (sns_score * Decimal("0.10") + media_score * Decimal("0.05")) / Decimal("0.15")

    async def _calculate_expert_survey_score(
        self,
        evaluation: Evaluation
    ) -> Decimal:
        """전문가 평가 및 설문 점수 계산"""
        # 실제로는 설문 데이터에서 조회
        return Decimal("80.0")

    def get_evaluations(
        self,
        skip: int = 0,
        limit: int = 100,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[Evaluation]:
        """평가 목록 조회"""
        query = self.db.query(Evaluation)

        if analyst_id:
            query = query.filter(Evaluation.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Evaluation.company_id == company_id)
        if status:
            query = query.filter(Evaluation.status == status)

        return query.order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()

    def get_evaluations_count(
        self,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> int:
        """평가 총 개수"""
        query = self.db.query(Evaluation)

        if analyst_id:
            query = query.filter(Evaluation.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Evaluation.company_id == company_id)
        if status:
            query = query.filter(Evaluation.status == status)

        return query.count()

    def get_evaluation(self, evaluation_id: UUID) -> Optional[Evaluation]:
        """평가 상세 조회"""
        return self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    def _get_current_period(self) -> str:
        """현재 기간 계산"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
    
    def get_evaluations_grouped_by_period(
        self,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """기간별 그룹화된 평가 조회 (기간>애널리스트>리포트)"""
        from sqlalchemy import func
        from app.models.analyst import Analyst
        from app.models.report import Report
        
        # 기간 필터
        query = self.db.query(Evaluation)
        if period:
            query = query.filter(Evaluation.evaluation_period == period)
        
        # 기간별 그룹화
        periods = {}
        evaluations = query.order_by(Evaluation.evaluation_period.desc(), Evaluation.created_at.desc()).all()
        
        for evaluation in evaluations:
            period_key = evaluation.evaluation_period
            
            if period_key not in periods:
                periods[period_key] = {
                    "period": period_key,
                    "analysts": {}
                }
            
            # 애널리스트별 그룹화
            analyst_id = str(evaluation.analyst_id)
            if analyst_id not in periods[period_key]["analysts"]:
                analyst = self.db.query(Analyst).filter(Analyst.id == evaluation.analyst_id).first()
                periods[period_key]["analysts"][analyst_id] = {
                    "analyst_id": analyst_id,
                    "analyst_name": analyst.name if analyst else "Unknown",
                    "analyst_firm": analyst.firm if analyst else "",
                    "reports": {}
                }
            
            # 리포트별 그룹화
            if evaluation.report_id:
                report_id = str(evaluation.report_id)
                if report_id not in periods[period_key]["analysts"][analyst_id]["reports"]:
                    report = self.db.query(Report).filter(Report.id == evaluation.report_id).first()
                    pub_date_str = ""
                    if report:
                        if report.publication_date:
                            if isinstance(report.publication_date, date):
                                pub_date_str = report.publication_date.isoformat()
                            else:
                                pub_date_str = str(report.publication_date)
                        elif report.created_at:
                            pub_date_str = report.created_at.date().isoformat()
                    
                    periods[period_key]["analysts"][analyst_id]["reports"][report_id] = {
                        "report_id": report_id,
                        "report_title": report.title if report else "Unknown",
                        "publication_date": pub_date_str,
                        "evaluations": []
                    }
                
                # 평가 추가
                periods[period_key]["analysts"][analyst_id]["reports"][report_id]["evaluations"].append({
                    "id": str(evaluation.id),
                    "final_score": float(evaluation.final_score) if evaluation.final_score else None,
                    "status": evaluation.status,
                    "created_at": evaluation.created_at.isoformat(),
                })
        
        # 딕셔너리를 리스트로 변환
        periods_list = []
        for period_key, period_data in periods.items():
            analysts_list = []
            for analyst_id, analyst_data in period_data["analysts"].items():
                reports_list = []
                for report_id, report_data in analyst_data["reports"].items():
                    reports_list.append(report_data)
                
                analyst_data["reports"] = reports_list
                analysts_list.append(analyst_data)
            
            periods_list.append({
                "period": period_key,
                "analysts": analysts_list,
                "total_evaluations": sum(
                    len(report["evaluations"])
                    for analyst in analysts_list
                    for report in analyst["reports"]
                )
            })
        
        return {
            "periods": periods_list,
            "total": len(evaluations)
        }


"""
통합 평가 서비스 - 리포트 분석, 기업실적, 평가 데이터 종합 평가
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from app.models.report import Report
from app.models.analyst import Analyst
from app.models.evaluation import Evaluation, EvaluationScore
from app.models.scorecard import Scorecard
from app.models.enums import EvaluationStatus
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
from app.services.report_service import ReportService
from app.services.evaluation_service import EvaluationService
from app.services.scorecard_service import ScorecardService


class ComprehensiveEvaluationService:
    """통합 평가 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluation_agent = EvaluationAgent(db)
        self.report_parsing_agent = ReportParsingAgent(db)
        self.report_service = ReportService(db)
        self.evaluation_service = EvaluationService(db)
        self.scorecard_service = ScorecardService(db)

    async def evaluate_analyst_comprehensive(
        self,
        analyst_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """애널리스트 통합 평가 실행"""
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_id}")

        # 기간 내 리포트 조회
        query = self.db.query(Report).filter(Report.analyst_id == analyst_id)
        if start_date:
            query = query.filter(Report.publication_date >= start_date.date())
        if end_date:
            query = query.filter(Report.publication_date <= end_date.date())
        
        reports = query.all()

        if not reports:
            return {
                "analyst_id": str(analyst_id),
                "analyst_name": analyst.name,
                "reports_evaluated": 0,
                "final_score": 0.0,
                "rank": None,
                "message": "평가할 리포트가 없습니다."
            }

        # 각 리포트별 평가 실행
        report_evaluations = []
        total_score = 0.0

        for report in reports:
            try:
                # 리포트 분석 (이미 분석되지 않은 경우)
                if report.status == "pending":
                    await self._analyze_report(report.id)

                # 리포트 평가
                evaluation_result = await self._evaluate_report(report.id, analyst_id)
                if evaluation_result:
                    report_evaluations.append(evaluation_result)
                    total_score += evaluation_result.get("final_score", 0.0)
            except Exception as e:
                print(f"리포트 평가 오류 (report_id={report.id}): {str(e)}")
                continue

        # 애널리스트 최종 점수 계산 (평균)
        final_score = total_score / len(report_evaluations) if report_evaluations else 0.0

        # 스코어카드 생성 또는 업데이트
        scorecard = await self._create_or_update_scorecard(
            analyst_id, final_score, report_evaluations
        )

        # 애널리스트 순위 계산
        rank = await self._calculate_analyst_rank(analyst_id, final_score)

        return {
            "analyst_id": str(analyst_id),
            "analyst_name": analyst.name,
            "reports_evaluated": len(report_evaluations),
            "report_evaluations": report_evaluations,
            "final_score": round(final_score, 2),
            "rank": rank,
            "scorecard_id": str(scorecard.id) if scorecard else None
        }

    async def _analyze_report(self, report_id: UUID) -> Dict[str, Any]:
        """리포트 자동 분석"""
        try:
            report = self.db.query(Report).filter(Report.id == report_id).first()
            if not report or not report.file_path:
                return {"status": "skipped", "reason": "PDF 파일이 없습니다."}

            # 리포트 파싱 실행
            result = await self.report_parsing_agent.parse_report(
                report_id,
                report.file_path
            )

            # 리포트 상태 업데이트
            report.status = "completed"
            self.db.commit()

            return {"status": "completed", "result": result}
        except Exception as e:
            print(f"리포트 분석 오류: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def _evaluate_report(self, report_id: UUID, analyst_id: UUID) -> Optional[Dict[str, Any]]:
        """리포트 평가"""
        try:
            # 평가 생성
            evaluation = Evaluation(
                analyst_id=analyst_id,
                report_id=report_id,
                status=EvaluationStatus.RUNNING.value
            )
            self.db.add(evaluation)
            self.db.commit()
            self.db.refresh(evaluation)

            # 평가 실행
            result = await self.evaluation_agent.evaluate_async(
                evaluation.id,
                report_id
            )

            return {
                "report_id": str(report_id),
                "evaluation_id": str(evaluation.id),
                "final_score": float(result.get("final_score", 0.0)),
                "scores": result.get("scores", {})
            }
        except Exception as e:
            print(f"리포트 평가 오류: {str(e)}")
            return None

    async def _create_or_update_scorecard(
        self,
        analyst_id: UUID,
        final_score: float,
        report_evaluations: List[Dict[str, Any]]
    ) -> Optional[Scorecard]:
        """스코어카드 생성 또는 업데이트"""
        try:
            # 기존 스코어카드 조회
            scorecard = self.db.query(Scorecard).filter(
                Scorecard.analyst_id == analyst_id
            ).order_by(Scorecard.created_at.desc()).first()

            # 리포트별 점수 집계
            kpi_scores = {}
            for eval_data in report_evaluations:
                scores = eval_data.get("scores", {})
                for kpi, score in scores.items():
                    if kpi not in kpi_scores:
                        kpi_scores[kpi] = []
                    kpi_scores[kpi].append(score)

            # 평균 계산
            avg_kpi_scores = {
                kpi: sum(scores) / len(scores) if scores else 0.0
                for kpi, scores in kpi_scores.items()
            }

            if scorecard:
                # 업데이트
                scorecard.final_score = Decimal(str(final_score))
                scorecard.kpi_scores = avg_kpi_scores
                scorecard.updated_at = datetime.now()
            else:
                # 생성
                scorecard = Scorecard(
                    analyst_id=analyst_id,
                    final_score=Decimal(str(final_score)),
                    kpi_scores=avg_kpi_scores
                )
                self.db.add(scorecard)

            self.db.commit()
            self.db.refresh(scorecard)

            return scorecard
        except Exception as e:
            print(f"스코어카드 생성/업데이트 오류: {str(e)}")
            self.db.rollback()
            return None

    async def _calculate_analyst_rank(
        self,
        analyst_id: UUID,
        final_score: float
    ) -> Optional[int]:
        """애널리스트 순위 계산"""
        try:
            # 모든 애널리스트의 최신 스코어카드 조회
            scorecards = self.db.query(Scorecard).order_by(
                Scorecard.final_score.desc()
            ).all()

            # 순위 계산
            rank = 1
            for scorecard in scorecards:
                if scorecard.analyst_id == analyst_id:
                    return rank
                rank += 1

            return None
        except Exception as e:
            print(f"순위 계산 오류: {str(e)}")
            return None


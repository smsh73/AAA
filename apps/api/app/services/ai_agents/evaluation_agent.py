"""
Evaluation Agent - 평가 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from app.models.evaluation import Evaluation, EvaluationScore
from app.models.enums import EvaluationStatus
from app.models.prediction import Prediction
from app.models.actual_result import ActualResult
from app.models.company import Company
from app.models.report import Report
from app.services.llm_service import LLMService
from app.services.perplexity_service import PerplexityService
from app.services.dart_service import DartService
from app.services.krx_service import KrxService
from datetime import datetime, timedelta


class EvaluationAgent:
    """평가 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        # LLMService는 지연 초기화 (API 키가 없어도 에러 방지)
        self._llm_service = None
        self.perplexity_service = PerplexityService()
        self.dart_service = DartService()
        self.krx_service = KrxService()
    
    @property
    def llm_service(self):
        """LLMService 지연 초기화"""
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service

    async def evaluate_async(
        self,
        evaluation_id: UUID,
        report_id: UUID
    ) -> Dict[str, Any]:
        """비동기 평가 실행"""
        evaluation = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # 1. 리포트에서 예측 정보 추출 (OpenAI)
        predictions = await self._extract_predictions(report_id)

        # 2. 실제 데이터 수집 (OpenDART, KRX, Perplexity 통합)
        actual_results = await self._collect_actual_data(predictions, report_id)

        # 3. 근거 분석 (Claude)
        reasoning_scores = await self._analyze_reasoning(predictions)

        # 4. 정확도 계산 (Gemini)
        accuracy_scores = await self._calculate_accuracy(predictions, actual_results)

        # 5. 통합 Scoring
        scores = self._calculate_scores(accuracy_scores, reasoning_scores, report_id, evaluation.analyst_id)

        # 6. 점수 저장
        for score_type, score_value in scores.items():
            eval_score = EvaluationScore(
                evaluation_id=evaluation_id,
                score_type=score_type,
                score_value=Decimal(str(score_value)),
                weight=self._get_weight(score_type),
            )
            self.db.add(eval_score)

        # 6. 최종 점수 계산 (가중치 적용)
        final_score = self._calculate_final_score(scores)
        evaluation.final_score = Decimal(str(final_score))
        evaluation.status = EvaluationStatus.COMPLETED.value
        self.db.commit()

        # 7. 평가 완료 후 스코어카드 자동 생성
        from app.services.evaluation_service import EvaluationService
        evaluation_service = EvaluationService(self.db)
        try:
            await evaluation_service.complete_evaluation(evaluation_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"스코어카드 생성 실패: {str(e)}")
            # 스코어카드 생성 실패해도 평가는 완료된 것으로 처리

        return {
            "evaluation_id": evaluation_id,
            "scores": scores,
            "final_score": final_score,
            "status": "completed"
        }

    async def _extract_predictions(self, report_id: UUID) -> list:
        """예측 정보 추출 - 이미 ReportParsingAgent에서 추출된 Prediction 사용"""
        # 리포트 파싱 시 이미 Prediction이 생성되었으므로 조회만 수행
        predictions = self.db.query(Prediction).filter(
            Prediction.report_id == report_id
        ).all()
        
        # Prediction이 없으면 빈 리스트 반환 (리포트 파싱이 완료되지 않았을 수 있음)
        return predictions

    async def _collect_actual_data(self, predictions: list, report_id: UUID) -> list:
        """실제 데이터 수집 (OpenDART, KRX, Perplexity 통합)"""
        actual_results = []
        
        # 리포트에서 기업 정보 가져오기
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report or not report.company_id:
            return actual_results
        
        company = self.db.query(Company).filter(Company.id == report.company_id).first()
        if not company:
            return actual_results
        
        for prediction in predictions:
            try:
                if prediction.prediction_type == "target_price":
                    # 목표주가 데이터 수집 (KRX API)
                    actual_result = await self._collect_target_price_actual(
                        company, prediction
                    )
                    if actual_result:
                        actual_results.append(actual_result)
                
                elif prediction.prediction_type in ["revenue", "operating_profit", "net_profit"]:
                    # 실적 데이터 수집 (OpenDART API)
                    actual_result = await self._collect_performance_actual(
                        company, prediction
                    )
                    if actual_result:
                        actual_results.append(actual_result)
                
                else:
                    # 기타 예측은 Perplexity로 수집
                    actual_result = await self._collect_other_actual(
                        company, prediction
                    )
                    if actual_result:
                        actual_results.append(actual_result)
                        
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"실제 데이터 수집 실패 (prediction {prediction.id}): {str(e)}")
                continue
        
        return actual_results
    
    async def _collect_target_price_actual(
        self,
        company: Company,
        prediction: Prediction
    ) -> Optional[ActualResult]:
        """목표주가 실제 데이터 수집 (KRX API)"""
        if not company.ticker:
            return None
        
        try:
            # 예측 기간 계산
            report = self.db.query(Report).filter(
                Report.id == prediction.report_id
            ).first()
            
            if not report:
                return None
            
            report_date = report.publication_date
            if isinstance(report_date, str):
                report_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            
            # 예측 기간 (예: 3개월, 6개월, 1년)
            period_days = 90  # 기본값 3개월
            if prediction.period:
                if "3개월" in prediction.period or "3M" in prediction.period:
                    period_days = 90
                elif "6개월" in prediction.period or "6M" in prediction.period:
                    period_days = 180
                elif "1년" in prediction.period or "1Y" in prediction.period:
                    period_days = 365
            
            end_date = datetime.now().date()
            start_date = report_date
            
            # KRX API로 주가 데이터 수집
            price_data = await self.krx_service.get_price_range(
                company.ticker,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if price_data and price_data.get("end_price"):
                actual_value = price_data["end_price"]
                
                # ActualResult 생성 또는 업데이트
                actual_result = self.db.query(ActualResult).filter(
                    ActualResult.prediction_id == prediction.id
                ).first()
                
                if not actual_result:
                    actual_result = ActualResult(
                        prediction_id=prediction.id,
                        company_id=company.id,
                        actual_value=str(actual_value),
                        period=prediction.period or "",
                        announcement_date=end_date,
                        source="KRX",
                        extra_data=price_data
                    )
                    self.db.add(actual_result)
                else:
                    actual_result.actual_value = str(actual_value)
                    actual_result.announcement_date = end_date
                    actual_result.extra_data = price_data
                
                self.db.commit()
                return actual_result
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"목표주가 데이터 수집 실패: {str(e)}")
        
        return None
    
    async def _collect_performance_actual(
        self,
        company: Company,
        prediction: Prediction
    ) -> Optional[ActualResult]:
        """실적 데이터 수집 (OpenDART API)"""
        try:
            # 회사 코드 찾기 (DART API)
            if not company.ticker:
                return None
            
            # 예측 기간에서 연도/분기 추출
            report = self.db.query(Report).filter(
                Report.id == prediction.report_id
            ).first()
            
            if not report:
                return None
            
            report_date = report.publication_date
            if isinstance(report_date, str):
                report_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            
            bsns_year = str(report_date.year)
            
            # 분기 결정
            quarter = (report_date.month - 1) // 3 + 1
            reprt_code_map = {
                1: "11013",  # 1분기
                2: "11012",  # 반기
                3: "11014",  # 3분기
                4: "11011"   # 사업보고서
            }
            reprt_code = reprt_code_map.get(quarter, "11011")
            
            # DART API로 실적 데이터 수집
            # 먼저 회사 코드 찾기
            companies = await self.dart_service.search_company_by_name(company.name_kr or company.name_en or "")
            
            if not companies:
                return None
            
            corp_code = companies[0].get("corp_code")
            if not corp_code:
                return None
            
            # 재무제표 조회
            performance_data = await self.dart_service.get_quarterly_performance(
                corp_code,
                bsns_year,
                reprt_code
            )
            
            # 예측 타입에 맞는 실제 값 추출
            actual_value = None
            metric_map = {
                "revenue": "revenue",
                "operating_profit": "operating_profit",
                "net_profit": "net_profit"
            }
            
            metric_key = metric_map.get(prediction.prediction_type)
            if metric_key and performance_data.get(metric_key):
                actual_value = performance_data[metric_key]
            
            if actual_value:
                # ActualResult 생성 또는 업데이트
                actual_result = self.db.query(ActualResult).filter(
                    ActualResult.prediction_id == prediction.id
                ).first()
                
                if not actual_result:
                    actual_result = ActualResult(
                        prediction_id=prediction.id,
                        company_id=company.id,
                        actual_value=str(actual_value),
                        period=prediction.period or "",
                        announcement_date=report_date,
                        source="OpenDART",
                        extra_data=performance_data
                    )
                    self.db.add(actual_result)
                else:
                    actual_result.actual_value = str(actual_value)
                    actual_result.announcement_date = report_date
                    actual_result.extra_data = performance_data
                
                self.db.commit()
                return actual_result
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"실적 데이터 수집 실패: {str(e)}")
        
        return None
    
    async def _collect_other_actual(
        self,
        company: Company,
        prediction: Prediction
    ) -> Optional[ActualResult]:
        """기타 예측 데이터 수집 (Perplexity)"""
        try:
            # Perplexity로 데이터 수집
            prompt = f"""
다음 예측에 대한 실제 데이터를 수집하세요:

기업: {company.name_kr or company.name_en}
예측 타입: {prediction.prediction_type}
예측 값: {prediction.predicted_value}
예측 기간: {prediction.period or "N/A"}

실제 데이터를 JSON 형식으로 반환하세요:
{{
  "actual_value": 실제값,
  "actual_date": "날짜",
  "data_source": "출처",
  "metadata": {{추가 정보}}
}}
"""
            result = await self.perplexity_service.search(prompt)
            
            # 결과 파싱 (실제 구현 필요)
            # 현재는 기본값 반환
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"기타 데이터 수집 실패: {str(e)}")
        
        return None

    async def _analyze_reasoning(self, predictions: list) -> Dict[str, float]:
        """근거 분석 (Claude)"""
        reasoning_scores = {}
        
        for prediction in predictions:
            if prediction.reasoning:
                prompt = f"""
다음 예측 근거를 분석하여 논리적 타당성을 평가하세요 (0-100점):

예측: {prediction.prediction_type}
근거: {prediction.reasoning}

평가 기준:
- 논리적 일관성
- 근거의 구체성
- 데이터 기반 분석 여부
"""
                result = await self.llm_service.generate("claude", prompt)
                # 점수 추출 (실제 구현 필요)
                reasoning_scores[prediction.id] = 85.0
        
        return reasoning_scores

    async def _calculate_accuracy(
        self,
        predictions: list,
        actual_results: list
    ) -> Dict[str, float]:
        """정확도 계산 (Gemini)"""
        accuracy_scores = {}
        
        for prediction in predictions:
            actual = next(
                (r for r in actual_results if r.prediction_id == prediction.id),
                None
            )
            
            if actual:
                # 괴리율 계산
                if prediction.prediction_type == "target_price":
                    deviation_rate = abs(
                        (float(actual.actual_value) - float(prediction.predicted_value)) /
                        float(prediction.predicted_value) * 100
                    )
                    accuracy = max(0, 100 - deviation_rate)
                    accuracy_scores[prediction.id] = accuracy
                elif prediction.prediction_type in ["revenue", "operating_profit", "net_profit"]:
                    # 가중 평균 오차율 계산
                    error_rate = abs(
                        (float(actual.actual_value) - float(prediction.predicted_value)) /
                        abs(float(actual.actual_value)) * 100
                    )
                    accuracy = max(0, 100 - error_rate)
                    accuracy_scores[prediction.id] = accuracy
        
        return accuracy_scores

    def _calculate_scores(
        self,
        accuracy_scores: Dict[str, float],
        reasoning_scores: Dict[str, float],
        report_id: UUID,
        analyst_id: UUID
    ) -> Dict[str, float]:
        """통합 점수 계산"""
        # KPI별 점수 계산
        scores = {
            "target_price_accuracy": self._calculate_target_price_score(accuracy_scores),
            "performance_accuracy": self._calculate_performance_score(accuracy_scores),
            "investment_logic_validity": sum(reasoning_scores.values()) / len(reasoning_scores) if reasoning_scores else 0,
            "risk_analysis_appropriateness": self._calculate_risk_analysis_score(report_id),
            "report_frequency": self._calculate_report_frequency_score(analyst_id),
            "sns_attention": self._calculate_sns_attention_score(analyst_id),
            "media_frequency": self._calculate_media_frequency_score(analyst_id),
        }
        
        return scores

    def _calculate_target_price_score(self, accuracy_scores: Dict[str, float]) -> float:
        """목표주가 정확도 점수 계산 - 실제 데이터 기반"""
        # Prediction 모델에서 target_price 타입만 필터링
        target_price_predictions = self.db.query(Prediction).filter(
            Prediction.prediction_type == "target_price"
        ).all()
        
        if not target_price_predictions:
            return 0.0
        
        # 각 예측에 대한 정확도 점수 수집
        target_price_scores = []
        for prediction in target_price_predictions:
            pred_id = str(prediction.id)
            if pred_id in accuracy_scores:
                target_price_scores.append(accuracy_scores[pred_id])
        
        if not target_price_scores:
            return 0.0
        
        # 평균 계산
        return sum(target_price_scores) / len(target_price_scores)

    def _calculate_performance_score(self, accuracy_scores: Dict[str, float]) -> float:
        """실적 추정 정확도 점수 계산 (가중 평균 오차율) - 실제 데이터 기반"""
        # revenue, operating_profit, net_profit 관련 예측만 필터링
        performance_types = ["revenue", "operating_profit", "net_profit"]
        performance_predictions = self.db.query(Prediction).filter(
            Prediction.prediction_type.in_(performance_types)
        ).all()
        
        if not performance_predictions:
            return 0.0
        
        # 가중치 정의 (영업이익 60%, 매출액 20%, 순이익 20%)
        type_weights = {
            "operating_profit": 0.60,
            "revenue": 0.20,
            "net_profit": 0.20
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for prediction in performance_predictions:
            pred_id = str(prediction.id)
            if pred_id in accuracy_scores:
                weight = type_weights.get(prediction.prediction_type, 0.0)
                weighted_sum += accuracy_scores[pred_id] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight

    def _calculate_risk_analysis_score(self, report_id: UUID) -> float:
        """리스크 분석 적정성 점수 계산"""
        from app.models.report import ReportSection
        
        # 리포트에서 risk 섹션 찾기
        risk_sections = self.db.query(ReportSection).filter(
            ReportSection.report_id == report_id,
            ReportSection.section_type == "risk"
        ).all()
        
        if not risk_sections:
            return 0.0  # 리스크 섹션이 없으면 0점
        
        # 리스크 섹션 내용 분석
        total_content_length = sum(len(section.content or "") for section in risk_sections)
        
        # 내용이 충분히 있으면 높은 점수 (최소 200자 이상)
        if total_content_length >= 200:
            return min(100.0, 60.0 + (total_content_length / 10))  # 200자 = 60점, 1000자 = 100점
        elif total_content_length >= 50:
            return 30.0 + (total_content_length / 5)  # 50자 = 30점, 200자 = 60점
        else:
            return total_content_length / 2  # 50자 미만 = 낮은 점수

    def _calculate_report_frequency_score(self, analyst_id: UUID) -> float:
        """리포트 발행 빈도 점수 계산"""
        from app.models.report import Report
        from datetime import datetime, timedelta
        
        # 최근 3개월 리포트 수 계산
        three_months_ago = datetime.now() - timedelta(days=90)
        
        recent_reports = self.db.query(Report).filter(
            Report.analyst_id == analyst_id,
            Report.created_at >= three_months_ago
        ).count()
        
        # 기준: 월 2개 리포트 = 100점
        # 3개월 기준 6개 리포트 = 100점
        if recent_reports >= 6:
            return 100.0
        elif recent_reports >= 4:
            return 80.0
        elif recent_reports >= 2:
            return 60.0
        elif recent_reports >= 1:
            return 40.0
        else:
            return 20.0

    def _calculate_sns_attention_score(self, analyst_id: UUID) -> float:
        """SNS 주목도 점수 계산 - 실제 데이터 수집 기반"""
        from app.models.data_collection_log import DataCollectionLog
        from datetime import datetime, timedelta
        
        # 최근 3개월 SNS 데이터 수집 로그 조회
        three_months_ago = datetime.now() - timedelta(days=90)
        
        sns_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == analyst_id,
            DataCollectionLog.collection_type == "sns",
            DataCollectionLog.status == "success",
            DataCollectionLog.created_at >= three_months_ago
        ).all()
        
        if not sns_logs:
            return 0.0
        
        # 수집된 데이터에서 주목도 지표 추출
        total_attention = 0.0
        valid_logs = 0
        
        for log in sns_logs:
            if log.collected_data:
                # SNS 데이터에서 주목도 지표 추출 (예: 좋아요, 리트윗, 댓글 수 등)
                attention_score = log.collected_data.get("attention_score", 0)
                if attention_score > 0:
                    total_attention += float(attention_score)
                    valid_logs += 1
        
        if valid_logs == 0:
            return 0.0
        
        # 평균 주목도 점수 계산 (0-100 스케일)
        avg_attention = total_attention / valid_logs
        
        # 점수 정규화 (기준: 평균 주목도 100 = 100점)
        # 실제 기준값은 데이터에 따라 조정 필요
        normalized_score = min(100.0, (avg_attention / 100.0) * 100.0)
        
        return round(normalized_score, 2)

    def _calculate_media_frequency_score(self, analyst_id: UUID) -> float:
        """미디어 언급 빈도 점수 계산 - 실제 데이터 수집 기반"""
        from app.models.data_collection_log import DataCollectionLog
        from datetime import datetime, timedelta
        
        # 최근 3개월 미디어 데이터 수집 로그 조회
        three_months_ago = datetime.now() - timedelta(days=90)
        
        media_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == analyst_id,
            DataCollectionLog.collection_type == "media",
            DataCollectionLog.status == "success",
            DataCollectionLog.created_at >= three_months_ago
        ).all()
        
        if not media_logs:
            return 0.0
        
        # 언급 빈도 계산 (월 평균 기준)
        total_mentions = len(media_logs)
        months = 3.0
        monthly_mentions = total_mentions / months
        
        # 기준: 월 10회 언급 = 100점
        if monthly_mentions >= 10:
            return 100.0
        elif monthly_mentions >= 7:
            return 80.0
        elif monthly_mentions >= 5:
            return 60.0
        elif monthly_mentions >= 3:
            return 40.0
        elif monthly_mentions >= 1:
            return 20.0
        else:
            return 10.0

    def _calculate_final_score(self, scores: Dict[str, float]) -> float:
        """가중치 적용한 최종 점수 계산"""
        weights = {
            "target_price_accuracy": 0.25,
            "performance_accuracy": 0.30,
            "investment_logic_validity": 0.15,
            "risk_analysis_appropriateness": 0.10,
            "report_frequency": 0.05,
            "sns_attention": 0.10,
            "media_frequency": 0.05,
        }
        
        # 가중치 합계 검증 (예외 발생)
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001:  # 부동소수점 오차 허용
            raise ValueError(
                f"가중치 합계가 1.0이 아닙니다: {total_weight}. "
                f"모든 KPI 가중치의 합은 정확히 1.0이어야 합니다."
            )
        
        # 모든 점수가 0-100 범위인지 검증
        for score_type, score_value in scores.items():
            if not (0.0 <= score_value <= 100.0):
                raise ValueError(
                    f"점수 범위 오류: {score_type} = {score_value}. "
                    f"모든 점수는 0-100 범위여야 합니다."
                )
        
        final_score = 0.0
        for score_type, score_value in scores.items():
            weight = weights.get(score_type, 0.0)
            if weight < 0 or weight > 1:
                raise ValueError(
                    f"가중치 범위 오류: {score_type} = {weight}. "
                    f"모든 가중치는 0-1 범위여야 합니다."
                )
            final_score += score_value * weight
        
        # 최종 점수도 0-100 범위로 정규화
        final_score = max(0.0, min(100.0, final_score))
        
        return round(final_score, 2)

    def _get_weight(self, score_type: str) -> Decimal:
        """점수 타입별 가중치"""
        weights = {
            "target_price_accuracy": Decimal("0.25"),
            "performance_accuracy": Decimal("0.30"),
            "investment_logic_validity": Decimal("0.15"),
            "risk_analysis_appropriateness": Decimal("0.10"),
            "report_frequency": Decimal("0.05"),
            "sns_attention": Decimal("0.10"),
            "media_frequency": Decimal("0.05"),
        }
        return weights.get(score_type, Decimal("0.0"))

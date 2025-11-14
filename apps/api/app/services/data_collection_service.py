"""
Data collection service
"""
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from app.services.perplexity_service import PerplexityService
from app.services.report_collection_service import ReportCollectionService
from app.services.comprehensive_evaluation_service import ComprehensiveEvaluationService
from app.services.dart_service import DartService
from app.services.google_search_service import GoogleSearchService
from app.models.data_collection_log import DataCollectionLog
from app.models.collection_job import CollectionJob
from app.schemas.data_collection import DataCollectionStartResponse, DataCollectionStatusResponse


class DataCollectionService:
    """데이터 수집 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.perplexity_service = PerplexityService()
        self.report_collection_service = ReportCollectionService(db)
        self.comprehensive_evaluation_service = ComprehensiveEvaluationService(db)
        self.dart_service = DartService()
        self.google_search = GoogleSearchService()

    async def start_collection(
        self,
        analyst_id: UUID,
        collection_types: List[str],
        start_date: date,
        end_date: date
    ) -> DataCollectionStartResponse:
        """데이터 수집 작업 시작"""
        from app.models.analyst import Analyst
        from app.tasks.data_collection_tasks import start_collection_job_task
        
        # 애널리스트 존재 확인
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_id}")
        
        # CollectionJob 생성
        job = CollectionJob(
            analyst_id=analyst_id,
            collection_types=collection_types,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
            status="pending",
            progress={ct: {"total": 0, "completed": 0, "failed": 0} for ct in collection_types},
            overall_progress="0.0"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # 예상 완료 시간 계산 (각 타입당 평균 5분 가정)
        estimated_minutes = len(collection_types) * 5
        estimated_completion = datetime.now() + timedelta(minutes=estimated_minutes)
        job.estimated_completion_time = estimated_completion
        self.db.commit()
        
        # Celery 태스크 시작
        start_collection_job_task.delay(str(job.id))
        
        return DataCollectionStartResponse(
            collection_job_id=job.id,
            status=job.status,
            estimated_completion_time=job.estimated_completion_time
        )

    def get_collection_status(self, collection_job_id: UUID) -> Optional[DataCollectionStatusResponse]:
        """데이터 수집 작업 상태 조회"""
        job = self.db.query(CollectionJob).filter(CollectionJob.id == collection_job_id).first()
        if not job:
            return None
        
        # 전체 진행률 계산
        total_tasks = 0
        completed_tasks = 0
        
        for ct, progress in job.progress.items():
            total = progress.get("total", 0)
            completed = progress.get("completed", 0)
            total_tasks += total
            completed_tasks += completed
        
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        return DataCollectionStatusResponse(
            collection_job_id=job.id,
            status=job.status,
            progress=job.progress,
            overall_progress=overall_progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )

    async def start_collection_for_analyst(self, analyst_id: UUID):
        """애널리스트별 자료수집 시작"""
        from app.models.analyst import Analyst
        from app.models.report import Report
        from app.services.ai_agents.data_collection_agent import DataCollectionAgent
        
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            return

        # 리포트 검색 및 다운로드
        reports = self.db.query(Report).filter(
            Report.analyst_id == analyst_id
        ).all()

        collection_agent = DataCollectionAgent(self.db)

        # 각 리포트별로 데이터 수집
        for report in reports:
            # 목표주가 데이터 수집
            if report.company_id:
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="target_price",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

                # 실적 데이터 수집
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="performance",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

            # SNS 데이터 수집
            report_date = report.publication_date
            if not report_date and report.created_at:
                report_date = report.created_at.date()
            
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="sns",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report_date.isoformat() if report_date else "",
                }
            )

            # 언론 데이터 수집
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="media",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report_date.isoformat() if report_date else "",
                }
            )

    def _log_message(
        self,
        collection_job_id: Optional[UUID],
        analyst_id: UUID,
        message: str,
        collection_type: str = "system"
    ):
        """실시간 로그 메시지 저장"""
        try:
            log = DataCollectionLog(
                analyst_id=analyst_id,
                collection_job_id=collection_job_id,
                collection_type=collection_type,
                log_message=message,
                status="info",
                collected_data={"message": message}
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            print(f"로그 메시지 저장 오류: {str(e)}")
            self.db.rollback()

    async def start_comprehensive_collection(
        self,
        analyst_id: UUID,
        collection_types: List[str],
        start_date: date,
        end_date: date,
        collection_job_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """통합 자료수집 시작 (리포트 수집, 분석, 평가 포함)"""
        from app.models.analyst import Analyst
        
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_id}")

        results = {
            "reports_collected": 0,
            "reports_analyzed": 0,
            "companies_data_collected": 0,
            "evaluation_data_collected": 0,
            "evaluations_completed": 0,
            "final_score": 0.0,
            "rank": None
        }

        # 1. 리포트 수집
        self._log_message(collection_job_id, analyst_id, "리포트 수집을 시작합니다...", "report_collection")
        try:
            report_results = await self.report_collection_service.collect_and_save_reports(
                analyst_id=analyst_id,
                collection_job_id=collection_job_id,
                start_date=start_date,
                end_date=end_date
            )
            results["reports_collected"] = report_results.get("reports_saved", 0)
            self._log_message(
                collection_job_id, analyst_id,
                f"리포트 {results['reports_collected']}개 수집 완료",
                "report_collection"
            )
        except Exception as e:
            self._log_message(
                collection_job_id, analyst_id,
                f"리포트 수집 오류: {str(e)}",
                "report_collection"
            )

        # 2. 리포트 자동 분석
        self._log_message(collection_job_id, analyst_id, "리포트 분석을 시작합니다...", "report_analysis")
        try:
            from app.models.report import Report
            reports = self.db.query(Report).filter(
                Report.analyst_id == analyst_id,
                Report.publication_date >= start_date,
                Report.publication_date <= end_date
            ).all()

            for report in reports:
                if report.status == "pending" and report.file_path:
                    try:
                        await self.comprehensive_evaluation_service._analyze_report(report.id)
                        results["reports_analyzed"] += 1
                    except Exception as e:
                        print(f"리포트 분석 오류 (report_id={report.id}): {str(e)}")
            
            self._log_message(
                collection_job_id, analyst_id,
                f"리포트 {results['reports_analyzed']}개 분석 완료",
                "report_analysis"
            )
        except Exception as e:
            self._log_message(
                collection_job_id, analyst_id,
                f"리포트 분석 오류: {str(e)}",
                "report_analysis"
            )

        # 3. 기업실적데이터 수집
        self._log_message(collection_job_id, analyst_id, "기업실적데이터 수집을 시작합니다...", "company_performance")
        try:
            from app.models.report import Report
            from app.models.company import Company
            from app.services.ai_agents.data_collection_agent import DataCollectionAgent
            
            reports = self.db.query(Report).filter(
                Report.analyst_id == analyst_id,
                Report.publication_date >= start_date,
                Report.publication_date <= end_date,
                Report.company_id.isnot(None)
            ).all()

            collection_agent = DataCollectionAgent(self.db)
            companies_processed = set()

            for report in reports:
                if report.company_id and report.company_id not in companies_processed:
                    company = self.db.query(Company).filter(Company.id == report.company_id).first()
                    if company:
                        # OpenDART API로 실적 데이터 수집
                        try:
                            if company.ticker:
                                # DART API로 실적 데이터 수집
                                await collection_agent.collect_data(
                                    analyst_id=analyst_id,
                                    collection_type="performance",
                                    params={
                                        "company_id": str(report.company_id),
                                        "report_id": str(report.id),
                                        "company_name": company.name_kr or company.name_en,
                                        "ticker": company.ticker
                                    },
                                    collection_job_id=collection_job_id
                                )
                                results["companies_data_collected"] += 1
                        except Exception as e:
                            print(f"기업실적 수집 오류: {str(e)}")
                        
                        companies_processed.add(report.company_id)
            
            self._log_message(
                collection_job_id, analyst_id,
                f"기업실적데이터 {results['companies_data_collected']}개 수집 완료",
                "company_performance"
            )
        except Exception as e:
            self._log_message(
                collection_job_id, analyst_id,
                f"기업실적데이터 수집 오류: {str(e)}",
                "company_performance"
            )

        # 4. 평가 KPI 데이터 수집
        self._log_message(collection_job_id, analyst_id, "평가 KPI 데이터 수집을 시작합니다...", "evaluation_kpi")
        try:
            from app.services.ai_agents.data_collection_agent import DataCollectionAgent
            from app.services.llm_service import LLMService
            
            collection_agent = DataCollectionAgent(self.db)
            llm_service = LLMService()

            # 구글 검색으로 평가 데이터 수집
            search_query = f"{analyst.name} {analyst.firm} 애널리스트 평가 KPI"
            google_results = await self.google_search.search_analyst_reports(
                analyst_name=analyst.name,
                securities_firm=analyst.firm
            )

            # OpenAI로 검색 결과 적합성 판단
            for result in google_results[:5]:  # 상위 5개만
                try:
                    # OpenAI로 적합성 판단
                    prompt = f"""
다음 검색 결과가 애널리스트 평가에 적합한지 판단해주세요.

검색 결과:
제목: {result.get('title', '')}
내용: {result.get('snippet', '')}

이 결과가 다음 평가 항목에 도움이 되는지 판단해주세요:
- 목표주가 정확도
- 실적 추정 정확도
- 투자 논리 타당성
- 리스크 분석 적정성
- 리포트 발행 빈도
- SNS 주목도
- 미디어 언급 빈도

응답 형식: JSON
{{
  "is_relevant": true/false,
  "relevance_score": 0-100,
  "helpful_for": ["kpi1", "kpi2"],
  "reason": "판단 근거"
}}
"""
                    llm_response = await llm_service.generate("openai", prompt)
                    content = llm_response.get("content", "")
                    
                    # JSON 파싱
                    import json
                    try:
                        if "```json" in content:
                            json_start = content.find("```json") + 7
                            json_end = content.find("```", json_start)
                            json_str = content[json_start:json_end].strip()
                            judgment = json.loads(json_str)
                        else:
                            json_start = content.find("{")
                            json_end = content.rfind("}") + 1
                            judgment = json.loads(content[json_start:json_end])
                        
                        if judgment.get("is_relevant", False):
                            # 데이터 저장
                            log = DataCollectionLog(
                                analyst_id=analyst_id,
                                collection_job_id=collection_job_id,
                                collection_type="evaluation_kpi",
                                collected_data={
                                    "source": "google_search",
                                    "title": result.get("title"),
                                    "link": result.get("link"),
                                    "judgment": judgment
                                },
                                status="success"
                            )
                            self.db.add(log)
                            results["evaluation_data_collected"] += 1
                    except:
                        pass
                except Exception as e:
                    print(f"KPI 데이터 판단 오류: {str(e)}")
                    continue

            self.db.commit()
            self._log_message(
                collection_job_id, analyst_id,
                f"평가 KPI 데이터 {results['evaluation_data_collected']}개 수집 완료",
                "evaluation_kpi"
            )
        except Exception as e:
            self._log_message(
                collection_job_id, analyst_id,
                f"평가 KPI 데이터 수집 오류: {str(e)}",
                "evaluation_kpi"
            )

        # 5. 통합 평가 실행
        self._log_message(collection_job_id, analyst_id, "통합 평가를 시작합니다...", "comprehensive_evaluation")
        try:
            evaluation_result = await self.comprehensive_evaluation_service.evaluate_analyst_comprehensive(
                analyst_id=analyst_id,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time())
            )
            results["evaluations_completed"] = evaluation_result.get("reports_evaluated", 0)
            results["final_score"] = evaluation_result.get("final_score", 0.0)
            results["rank"] = evaluation_result.get("rank")
            
            self._log_message(
                collection_job_id, analyst_id,
                f"통합 평가 완료: 최종 점수 {results['final_score']:.2f}, 순위 {results['rank']}",
                "comprehensive_evaluation"
            )
        except Exception as e:
            self._log_message(
                collection_job_id, analyst_id,
                f"통합 평가 오류: {str(e)}",
                "comprehensive_evaluation"
            )

        return results


# Mix of Agents 추론 알고리즘 상세 설계

## 1. 개요

여러 AI 모델(OpenAI, Claude, Gemini, Perplexity)을 협력적으로 활용하여 애널리스트 보고서를 평가하는 분산 추론 시스템입니다.

본 시스템은 "AI가 찾은 스타 애널리스트" 어워즈를 위한 3단계 심사 프로세스 중 1단계 AI 정량 분석을 담당하며, 2단계 SNS·시장 반응 분석과 3단계 전문가 평가 및 설문과 통합되어 최종 평가를 수행합니다.

## 2. Agent 역할 정의

### 2.1 OpenAI Agent (GPT-4)
**역할**: 보고서 구조 분석 및 핵심 예측 추출

**기능**:
- PDF/Word 보고서를 텍스트로 변환
- 보고서 구조 분석 (섹션별 분류)
- 예측 항목 자동 추출
- 구조화된 데이터 생성 (JSON)

**입력**:
```json
{
  "report_text": "원본 보고서 텍스트",
  "report_metadata": {
    "analyst_name": "애널리스트명",
    "company": "대상 기업",
    "date": "작성일",
    "securities_firm": "증권사명"
  }
}
```

**출력**:
```json
{
  "predictions": [
    {
      "type": "revenue",
      "predicted_value": 1000000,
      "unit": "억원",
      "period": "2024Q1",
      "reasoning": "예측 근거 텍스트"
    },
    {
      "type": "operating_profit",
      "predicted_value": 500000,
      "unit": "억원",
      "period": "2024Q1",
      "reasoning": "예측 근거 텍스트"
    },
    {
      "type": "target_price",
      "predicted_value": 50000,
      "unit": "원",
      "period": "2024-06",
      "reasoning": "예측 근거 텍스트"
    },
    {
      "type": "investment_opinion",
      "predicted_value": "Buy",
      "period": "2024-06",
      "reasoning": "예측 근거 텍스트"
    }
  ],
  "confidence_score": 0.85
}
```

### 2.2 Perplexity Agent
**역할**: 외부 데이터 수집 및 사실 검증

**기능**:
- 실적 데이터 검색 및 수집
- 뉴스 및 공시 정보 수집
- 시장 환경 데이터 수집
- 데이터 출처 검증

**입력**:
```json
{
  "company_name": "대상 기업명",
  "prediction_period": "2024Q1",
  "prediction_types": ["revenue", "operating_profit"],
  "report_date": "2023-12-01"
}
```

**출력**:
```json
{
  "actual_results": [
    {
      "type": "revenue",
      "actual_value": 950000,
      "unit": "억원",
      "period": "2024Q1",
      "source": "DART 공시",
      "source_url": "https://...",
      "reliability": "high"
    },
    {
      "type": "operating_profit",
      "actual_value": 480000,
      "unit": "억원",
      "period": "2024Q1",
      "source": "DART 공시",
      "source_url": "https://...",
      "reliability": "high"
    }
  ],
  "market_data": {
    "stock_price": {
      "date": "2024-06-30",
      "price": 48000,
      "source": "한국거래소"
    },
    "market_trend": "상승",
    "industry_performance": "평균"
  },
  "news_summary": [
    {
      "title": "기업명, 2024Q1 실적 발표",
      "date": "2024-05-15",
      "relevance": "high"
    }
  ]
}
```

### 2.3 Claude Agent (Claude 3.5 Sonnet)
**역할**: 예측 근거 분석 및 논리 검증

**기능**:
- 예측 근거의 논리 일관성 평가
- 데이터 근거 충실도 검증
- 시나리오 분석 깊이 평가
- 근거 품질 점수 산출

**입력**:
```json
{
  "predictions": [
    {
      "type": "revenue",
      "predicted_value": 1000000,
      "reasoning": "예측 근거 텍스트"
    }
  ],
  "report_context": "보고서 전체 맥락",
  "market_data": "시장 환경 데이터"
}
```

**출력**:
```json
{
  "reasoning_quality_scores": [
    {
      "prediction_type": "revenue",
      "logical_consistency": 0.85,
      "data_support": 0.90,
      "scenario_depth": 0.80,
      "overall_quality": 0.85,
      "analysis": "근거 분석 텍스트"
    }
  ],
  "reasoning_quality_score": 0.85,
  "strengths": [
    "강점 1",
    "강점 2"
  ],
  "weaknesses": [
    "약점 1",
    "약점 2"
  ]
}
```

### 2.4 Gemini Agent (Gemini Pro)
**역할**: 실적 데이터 검증 및 비교 분석

**기능**:
- 예측 vs 실제 비교 분석
- 정확도 계산
- 오차율 분석
- 트렌드 분석

**입력**:
```json
{
  "predictions": [
    {
      "type": "revenue",
      "predicted_value": 1000000,
      "period": "2024Q1"
    }
  ],
  "actual_results": [
    {
      "type": "revenue",
      "actual_value": 950000,
      "period": "2024Q1"
    }
  ],
  "market_context": "시장 환경 데이터"
}
```

**출력**:
```json
{
  "accuracy_analysis": [
    {
      "prediction_type": "revenue",
      "predicted_value": 1000000,
      "actual_value": 950000,
      "error_rate": 0.05,
      "error_absolute": 50000,
      "accuracy_score": 0.95,
      "direction_correct": true,
      "analysis": "분석 텍스트"
    }
  ],
  "overall_accuracy_score": 0.95,
  "trend_analysis": {
    "prediction_accuracy_trend": "개선",
    "market_impact": "중립적"
  }
}
```

## 3. 추론 알고리즘 플로우

### 3.1 전체 프로세스

```
1. 보고서 업로드 및 전처리
   │
   ├─> OpenAI Agent: 보고서 파싱 및 예측 추출
   │   └─> 구조화된 예측 데이터 생성
   │
   ├─> Perplexity Agent: 실제 데이터 수집 (병렬 실행)
   │   └─> 실적 데이터, 시장 데이터, 뉴스 수집
   │
   ├─> Claude Agent: 근거 분석 (예측 데이터 기반)
   │   └─> 근거 품질 점수 산출
   │
   ├─> Gemini Agent: 정확도 계산 (예측 vs 실제)
   │   └─> 정확도 점수 산출
   │
   └─> Ensemble Layer: 최종 Scoring
       └─> 가중 평균으로 최종 점수 계산
```

### 3.2 병렬 처리 전략

```
시작
 │
 ├─> OpenAI Agent (보고서 파싱)
 │   └─> 예측 데이터 추출 완료
 │
 └─> Perplexity Agent (데이터 수집) [병렬 실행]
     └─> 실제 데이터 수집 완료
 │
 ├─> Claude Agent (근거 분석)
 │   └─> 근거 품질 점수 산출
 │
 └─> Gemini Agent (정확도 계산)
     └─> 정확도 점수 산출
 │
 └─> Ensemble Scoring
     └─> 최종 점수 산출
```

### 3.3 의사결정 로직

#### 3.3.1 에러 처리
- 각 Agent 실패 시 재시도 (최대 3회)
- Agent별 대체 모델 준비
- 부분 실패 시에도 진행 가능한 구조

#### 3.3.2 결과 검증
- 각 Agent 결과의 신뢰도 점수 확인
- 이상치 탐지 및 플래그
- 수동 검증 필요 시 플래그 설정

## 4. 3단계 심사 프로세스 통합

### 4.1 전체 심사 프로세스

```
1단계: AI 정량 분석 (Mix of Agents)
   ├─> OpenAI Agent: 보고서 파싱 및 예측 추출
   ├─> Perplexity Agent: 실제 데이터 수집
   ├─> Claude Agent: 근거 분석
   ├─> Gemini Agent: 정확도 계산
   └─> AI 정량 분석 점수 산출

2단계: SNS·시장 반응 분석
   ├─> SNS 언급량 수집 및 분석
   ├─> 바이럴 지수 계산
   └─> 투자자 커뮤니티 반응 분석

3단계: 전문가 평가 및 설문
   ├─> 운용사/리서치센터 설문
   └─> 리테일 투자자 설문

최종 Scoring: 3단계 결과 통합
```

### 4.2 1단계: AI 정량 분석 점수

#### 4.2.1 가중치 설정

```python
ai_quantitative_weights = {
    "report_volume": 0.20,           # 리포트 생산량
    "stock_leading_accuracy": 0.50,  # 종목 리딩 정확도
    "industry_analysis_depth": 0.30  # 산업별 분석 깊이
}
```

#### 4.2.2 AI 정량 분석 점수 계산

```python
ai_quantitative_score = (
    report_volume_score * 0.20 +
    stock_leading_accuracy_score * 0.50 +
    industry_analysis_depth_score * 0.30
)
```

### 4.3 2단계: SNS·시장 반응 점수

#### 4.3.1 가중치 설정

```python
sns_market_weights = {
    "sns_mention_count": 0.40,      # SNS 언급량
    "viral_index": 0.30,            # 바이럴 지수
    "community_reaction": 0.30      # 투자자 커뮤니티 반응
}
```

#### 4.3.2 SNS·시장 반응 점수 계산

```python
sns_market_score = (
    sns_mention_score * 0.40 +
    viral_index_score * 0.30 +
    community_reaction_score * 0.30
)
```

### 4.4 3단계: 전문가 평가 및 설문 점수

#### 4.4.1 가중치 설정

```python
expert_survey_weights = {
    "institutional_survey": 0.60,    # 운용사/리서치센터 설문
    "retail_survey": 0.40            # 리테일 투자자 설문
}
```

#### 4.4.2 전문가 평가 및 설문 점수 계산

```python
expert_survey_score = (
    institutional_survey_score * 0.60 +
    retail_survey_score * 0.40
)
```

### 4.5 최종 Ensemble Scoring

#### 4.5.1 최종 가중치 설정

```python
final_weights = {
    "ai_quantitative_score": 0.40,   # 1단계: AI 정량 분석
    "sns_market_score": 0.30,         # 2단계: SNS·시장 반응
    "expert_survey_score": 0.30       # 3단계: 전문가 평가 및 설문
}
```

#### 4.5.2 최종 점수 계산

```python
final_score = (
    ai_quantitative_score * 0.40 +
    sns_market_score * 0.30 +
    expert_survey_score * 0.30
)
```


## 5. 구현 예시 (의사코드)

### 5.1 메인 오케스트레이션

```python
async def evaluate_analyst_report(report_file):
    # 1단계: AI 정량 분석
    # 1. 보고서 파싱
    predictions = await openai_agent.parse_report(report_file)
    
    # 2. 데이터 수집 (병렬)
    actual_data = await perplexity_agent.collect_data(
        company=predictions.company,
        period=predictions.period
    )
    
    # 3. 근거 분석
    reasoning_scores = await claude_agent.analyze_reasoning(
        predictions=predictions
    )
    
    # 4. 정확도 계산
    accuracy_scores = await gemini_agent.calculate_accuracy(
        predictions=predictions,
        actual_results=actual_data
    )
    
    # AI 정량 분석 점수 계산
    ai_quantitative_score = calculate_ai_quantitative_score(
        report_volume=calculate_report_volume(predictions),
        stock_leading_accuracy=accuracy_scores,
        industry_analysis_depth=reasoning_scores
    )
    
    # 2단계: SNS·시장 반응 분석
    sns_market_score = await analyze_sns_market_reaction(
        report_id=report_file.id,
        analyst_name=predictions.analyst_name,
        company_name=predictions.company
    )
    
    # 3단계: 전문가 평가 및 설문
    expert_survey_score = await get_expert_survey_score(
        report_id=report_file.id,
        analyst_id=predictions.analyst_id
    )
    
    # 최종 Scoring (3단계 통합)
    final_score = (
        ai_quantitative_score * 0.40 +
        sns_market_score * 0.30 +
        expert_survey_score * 0.30
    )
    
    return EvaluationResult(
        final_score=final_score,
        ai_quantitative_score=ai_quantitative_score,
        sns_market_score=sns_market_score,
        expert_survey_score=expert_survey_score,
        details=...
    )
```

### 5.2 Agent 구현 예시

```python
class OpenAIAgent:
    async def parse_report(self, report_text):
        prompt = f"""
        다음 애널리스트 보고서에서 예측 항목을 추출하세요:
        {report_text}
        
        출력 형식: JSON
        """
        response = await openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return parse_json(response.choices[0].message.content)
```

## 6. 성능 최적화

### 6.1 캐싱 전략
- 보고서 파싱 결과 캐싱
- 실적 데이터 캐싱 (TTL: 1일)
- API 응답 캐싱

### 6.2 배치 처리
- 여러 보고서를 배치로 처리
- API 호출 최소화

### 6.3 비동기 처리
- 모든 Agent 호출을 비동기로 처리
- 병렬 실행으로 처리 시간 단축

## 7. 모니터링 및 로깅

- 각 Agent 호출 시간 측정
- API 비용 추적
- 에러 발생 시 알림
- 결과 품질 모니터링


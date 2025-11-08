'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Table from '@/components/UI/Table'
import RadarChartComponent from '@/components/Charts/RadarChart'

interface EvaluationDetail {
  id: string
  report_id: string
  analyst_id: string
  company_id?: string
  evaluation_period: string
  evaluation_date: string
  final_score?: number
  ai_quantitative_score?: number
  sns_market_score?: number
  expert_survey_score?: number
  status: string
}

interface EvaluationScore {
  id: string
  score_type: string
  score_value: number
  weight: number
}

export default function EvaluationDetailPage() {
  const params = useParams()
  const evaluationId = params.id as string
  
  const [evaluation, setEvaluation] = useState<EvaluationDetail | null>(null)
  const [scores, setScores] = useState<EvaluationScore[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (evaluationId) {
      loadEvaluation()
      loadScores()
    }
  }, [evaluationId])

  const loadEvaluation = async () => {
    try {
      const res = await api.get(`/api/evaluations/${evaluationId}`)
      setEvaluation(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const loadScores = async () => {
    try {
      const res = await api.get(`/api/evaluations/${evaluationId}/scores`)
      setScores(res.data || [])
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          로딩 중...
        </div>
      </div>
    )
  }

  if (!evaluation) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          평가를 찾을 수 없습니다.
        </div>
      </div>
    )
  }

  const scoreColumns = [
    { key: 'score_type', label: '점수 타입' },
    { 
      key: 'score_value', 
      label: '점수',
      render: (score: EvaluationScore) => `${score.score_value.toFixed(2)}점`
    },
    { 
      key: 'weight', 
      label: '가중치',
      render: (score: EvaluationScore) => `${(score.weight * 100).toFixed(1)}%`
    },
  ]

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">평가 상세</h1>
        <p className="fnguide-page-subtitle">평가 기간: {evaluation.evaluation_period}</p>
      </div>

      <div className="fnguide-grid fnguide-grid-4" style={{ marginBottom: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginBottom: '8px' }}>
              최종 점수
            </div>
            <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--fnguide-primary)' }}>
              {evaluation.final_score ? evaluation.final_score.toFixed(2) : '-'}
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginBottom: '8px' }}>
              AI 정량 분석 (40%)
            </div>
            <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--fnguide-primary)' }}>
              {evaluation.ai_quantitative_score ? evaluation.ai_quantitative_score.toFixed(2) : '-'}
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginBottom: '8px' }}>
              SNS·시장 반응 (30%)
            </div>
            <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--fnguide-primary)' }}>
              {evaluation.sns_market_score ? evaluation.sns_market_score.toFixed(2) : '-'}
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginBottom: '8px' }}>
              전문가 평가 (30%)
            </div>
            <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--fnguide-primary)' }}>
              {evaluation.expert_survey_score ? evaluation.expert_survey_score.toFixed(2) : '-'}
            </div>
          </div>
        </Card>
      </div>

      <div className="fnguide-grid fnguide-grid-2">
        <Card title="세부 점수">
          {scores.length > 0 ? (
            <Table
              columns={scoreColumns}
              data={scores}
              keyExtractor={(item) => item.id}
            />
          ) : (
            <p style={{ color: 'var(--fnguide-gray-400)' }}>세부 점수가 없습니다.</p>
          )}
        </Card>

        <Card title="점수 시각화">
          {scores.length > 0 ? (
            <RadarChartComponent
              data={scores.map((score) => ({
                name: score.score_type.replace(/_/g, ' '),
                value: score.score_value,
              }))}
              name="점수"
            />
          ) : (
            <p style={{ color: 'var(--fnguide-gray-400)' }}>데이터가 없습니다.</p>
          )}
        </Card>
      </div>
    </div>
  )
}


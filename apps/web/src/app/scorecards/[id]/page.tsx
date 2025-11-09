'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'

interface ScorecardDetail {
  id: string
  analyst_id: string
  company_id?: string
  period: string
  final_score: number
  ranking?: number
  scorecard_data: {
    evaluation_id?: string
    scores?: Record<string, number>
    summary?: string
    analyst?: {
      id: string
      name: string
      firm: string
      sector?: string
    }
    company?: {
      id: string
      name: string
      ticker?: string
      sector?: string
    }
    evaluation?: {
      id: string
      status: string
      final_score?: number
      evaluation_period?: string
    }
    reports?: Array<{
      id: string
      title: string
      publication_date: string
      status: string
    }>
    evaluation_scores?: Array<{
      score_type: string
      score_value: number
      weight?: number
    }>
  }
  created_at: string
}

export default function ScorecardDetailPage() {
  const params = useParams()
  const scorecardId = params.id as string
  
  const [scorecard, setScorecard] = useState<ScorecardDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (scorecardId) {
      loadScorecard()
    }
  }, [scorecardId])

  const loadScorecard = async () => {
    try {
      const res = await api.get(`/api/scorecards/${scorecardId}`)
      setScorecard(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
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

  if (!scorecard) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          스코어카드를 찾을 수 없습니다.
        </div>
      </div>
    )
  }

  const analyst = scorecard.scorecard_data?.analyst
  const company = scorecard.scorecard_data?.company
  const evaluation = scorecard.scorecard_data?.evaluation
  const reports = scorecard.scorecard_data?.reports || []
  const evaluationScores = scorecard.scorecard_data?.evaluation_scores || []
  const kpiScores = scorecard.scorecard_data?.scores || {}

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">스코어카드 상세</h1>
        <p className="fnguide-page-subtitle">기간: {scorecard.period}</p>
      </div>

      {/* 기간 > 애널리스트 > 리포트 > 평가 구조 표시 */}
      <div style={{ marginBottom: '24px' }}>
        <Card title="기본 정보">
          <div className="fnguide-grid fnguide-grid-2" style={{ gap: '16px' }}>
            <div>
              <div style={{ marginBottom: '8px' }}>
                <strong>기간:</strong> {scorecard.period}
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>순위:</strong> {scorecard.ranking ? `${scorecard.ranking}위` : '-'}
              </div>
              <div>
                <strong>최종 점수:</strong>{' '}
                <span style={{ fontSize: '24px', fontWeight: 700, color: 'var(--fnguide-primary)' }}>
                  {scorecard.final_score.toFixed(2)}점
                </span>
              </div>
            </div>
            <div>
              {analyst && (
                <div style={{ marginBottom: '8px' }}>
                  <strong>애널리스트:</strong>{' '}
                  <a href={`/analysts/${analyst.id}`} style={{ color: 'var(--fnguide-primary)' }}>
                    {analyst.name} ({analyst.firm})
                  </a>
                </div>
              )}
              {company && (
                <div style={{ marginBottom: '8px' }}>
                  <strong>기업:</strong>{' '}
                  <a href={`/companies/${company.id}`} style={{ color: 'var(--fnguide-primary)' }}>
                    {company.name} {company.ticker && `(${company.ticker})`}
                  </a>
                </div>
              )}
              {evaluation && (
                <div>
                  <strong>평가:</strong>{' '}
                  <a href={`/evaluations/${evaluation.id}`} style={{ color: 'var(--fnguide-primary)' }}>
                    {evaluation.status} {evaluation.final_score && `(${evaluation.final_score.toFixed(2)}점)`}
                  </a>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* 리포트 목록 */}
      {reports.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <Card title="관련 리포트">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {reports.map((report) => (
                <div key={report.id} style={{ 
                  padding: '12px', 
                  border: '1px solid var(--fnguide-gray-200)', 
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <a href={`/reports/${report.id}`} style={{ 
                      color: 'var(--fnguide-primary)',
                      fontWeight: 500
                    }}>
                      {report.title}
                    </a>
                    <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginTop: '4px' }}>
                      발행일: {report.publication_date} | 상태: {report.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* KPI 점수 상세 */}
      <div className="fnguide-grid fnguide-grid-2" style={{ marginBottom: '24px' }}>
        <Card title="KPI 점수 상세">
          {Object.keys(kpiScores).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {Object.entries(kpiScores).map(([kpi, score]) => (
                <div key={kpi} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  padding: '8px',
                  backgroundColor: 'var(--fnguide-gray-50)',
                  borderRadius: '4px'
                }}>
                  <span style={{ fontWeight: 500 }}>
                    {kpi.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--fnguide-primary)' }}>
                    {typeof score === 'number' ? score.toFixed(2) : score}점
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--fnguide-gray-400)' }}>KPI 점수 데이터가 없습니다.</p>
          )}
        </Card>

        <Card title="평가 점수 상세">
          {evaluationScores.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {evaluationScores.map((es, idx) => (
                <div key={idx} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  padding: '8px',
                  backgroundColor: 'var(--fnguide-gray-50)',
                  borderRadius: '4px'
                }}>
                  <div>
                    <div style={{ fontWeight: 500 }}>
                      {es.score_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    {es.weight && (
                      <div style={{ fontSize: '12px', color: 'var(--fnguide-gray-500)' }}>
                        가중치: {(es.weight * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                  <span style={{ fontWeight: 600, color: 'var(--fnguide-primary)' }}>
                    {es.score_value.toFixed(2)}점
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--fnguide-gray-400)' }}>평가 점수 데이터가 없습니다.</p>
          )}
        </Card>
      </div>
    </div>
  )
}


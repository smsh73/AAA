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
  scorecard_data: any
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

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">스코어카드 상세</h1>
        <p className="fnguide-page-subtitle">기간: {scorecard.period}</p>
      </div>

      <div className="fnguide-grid fnguide-grid-2" style={{ marginBottom: '24px' }}>
        <Card title="기본 정보">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <strong>순위:</strong> {scorecard.ranking ? `${scorecard.ranking}위` : '-'}
            </div>
            <div>
              <strong>최종 점수:</strong>{' '}
              <span style={{ fontSize: '20px', fontWeight: 700, color: 'var(--fnguide-primary)' }}>
                {scorecard.final_score.toFixed(2)}점
              </span>
            </div>
            <div>
              <strong>기간:</strong> {scorecard.period}
            </div>
          </div>
        </Card>

        <Card title="스코어카드 데이터">
          <pre style={{ 
            backgroundColor: 'var(--fnguide-gray-100)', 
            padding: '16px', 
            borderRadius: '8px',
            overflow: 'auto',
            fontSize: '12px'
          }}>
            {JSON.stringify(scorecard.scorecard_data, null, 2)}
          </pre>
        </Card>
      </div>
    </div>
  )
}


'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Scorecard {
  id: string
  analyst_id: string
  company_id?: string
  period: string
  final_score: number
  ranking?: number
}

export default function ScorecardsPage() {
  const [scorecards, setScorecards] = useState<Scorecard[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('')

  useEffect(() => {
    loadScorecards()
  }, [period])

  const loadScorecards = async () => {
    try {
      const params: any = {}
      if (period) params.period = period
      
      const res = await api.get('/api/scorecards', { params })
      setScorecards(res.data || [])
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const columns = [
    { 
      key: 'ranking', 
      label: '순위',
      render: (scorecard: Scorecard) => scorecard.ranking || '-'
    },
    { key: 'period', label: '기간' },
    { 
      key: 'final_score', 
      label: '최종 점수',
      render: (scorecard: Scorecard) => `${scorecard.final_score.toFixed(2)}점`
    },
    { 
      key: 'actions', 
      label: '작업',
      render: (scorecard: Scorecard) => (
        <Link href={`/scorecards/${scorecard.id}`}>
          <Button variant="secondary" size="sm">상세</Button>
        </Link>
      )
    },
  ]

  if (loading) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          로딩 중...
        </div>
      </div>
    )
  }

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="fnguide-page-title">스코어카드</h1>
          <p className="fnguide-page-subtitle">스코어카드 목록 및 랭킹</p>
        </div>
        <Link href="/scorecards/ranking">
          <Button variant="primary">랭킹 보기</Button>
        </Link>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <Card title="기간 필터">
        <div className="fnguide-form-group" style={{ marginBottom: 0 }}>
          <label className="fnguide-form-label">기간 (예: 2025-Q1)</label>
          <input
            type="text"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="fnguide-form-input"
            placeholder="2025-Q1"
            style={{ maxWidth: '200px' }}
          />
        </div>
        </Card>
      </div>

      <Card>
        <Table
          columns={columns}
          data={scorecards}
          keyExtractor={(item) => item.id}
        />
      </Card>
    </div>
  )
}


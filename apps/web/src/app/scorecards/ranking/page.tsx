'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'

interface Ranking {
  id: string
  analyst_id: string
  company_id?: string
  period: string
  final_score: number
  ranking?: number
}

export default function RankingPage() {
  const [rankings, setRankings] = useState<Ranking[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('')
  const [total, setTotal] = useState(0)

  useEffect(() => {
    loadRankings()
  }, [period])

  const loadRankings = async () => {
    try {
      const params: any = { limit: 100 }
      if (period) params.period = period
      
      const res = await api.get('/api/scorecards/ranking', { params })
      setRankings(res.data.rankings || [])
      setTotal(res.data.total || 0)
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
      render: (item: Ranking) => {
        const rank = item.ranking || rankings.indexOf(item) + 1
        if (rank === 1) return '🥇 1위'
        if (rank === 2) return '🥈 2위'
        if (rank === 3) return '🥉 3위'
        return `${rank}위`
      }
    },
    { key: 'period', label: '기간' },
    { 
      key: 'final_score', 
      label: '최종 점수',
      render: (item: Ranking) => (
        <span style={{ fontWeight: 600, color: 'var(--fnguide-primary)' }}>
          {item.final_score.toFixed(2)}점
        </span>
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
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">랭킹</h1>
        <p className="fnguide-page-subtitle">스코어카드 랭킹</p>
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
          data={rankings}
          keyExtractor={(item) => item.id}
        />
        <div style={{ marginTop: '16px', color: 'var(--fnguide-gray-500)' }}>
          전체 {total}건
        </div>
      </Card>
    </div>
  )
}


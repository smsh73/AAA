'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'

interface Award {
  id: string
  analyst_id: string
  award_type: string
  award_category: string
  period: string
  rank: number
}

export default function AwardsPage() {
  const [awards, setAwards] = useState<Award[]>([])
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(new Date().getFullYear())

  useEffect(() => {
    api.get('/api/awards', { params: { year } })
      .then((res) => {
        setAwards(res.data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [year])

  const columns = [
    { key: 'rank', label: '순위' },
    { key: 'award_category', label: '카테고리' },
    { 
      key: 'award_type', 
      label: '어워드 타입',
      render: (award: Award) => {
        const typeMap: Record<string, string> = {
          gold: '🥇 금상',
          silver: '🥈 은상',
          bronze: '🥉 동상',
        }
        return typeMap[award.award_type] || award.award_type
      }
    },
    { key: 'period', label: '기간' },
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
        <h1 className="fnguide-page-title">어워즈</h1>
        <p className="fnguide-page-subtitle">AI가 찾은 스타 애널리스트 어워즈 수상자</p>
      </div>

      <Card title="연도별 필터" style={{ marginBottom: '24px' }}>
        <div className="fnguide-form-group" style={{ marginBottom: 0 }}>
          <label className="fnguide-form-label">연도</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            className="fnguide-form-input"
            style={{ maxWidth: '200px' }}
          />
        </div>
      </Card>

      <Card>
        <Table
          columns={columns}
          data={awards}
          keyExtractor={(item) => item.id}
        />
      </Card>
    </div>
  )
}


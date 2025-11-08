'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Evaluation {
  id: string
  report_id: string
  analyst_id: string
  company_id?: string
  evaluation_period: string
  final_score?: number
  status: string
  created_at: string
}

export default function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const limit = 20

  useEffect(() => {
    loadEvaluations()
  }, [skip])

  const loadEvaluations = async () => {
    try {
      const res = await api.get('/api/evaluations', {
        params: { skip, limit }
      })
      setEvaluations(res.data.evaluations || [])
      setTotal(res.data.total || 0)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const columns = [
    { key: 'evaluation_period', label: '평가 기간' },
    { 
      key: 'final_score', 
      label: '최종 점수',
      render: (evaluation: Evaluation) => 
        evaluation.final_score ? `${evaluation.final_score.toFixed(2)}점` : '-'
    },
    { 
      key: 'status', 
      label: '상태',
      render: (evaluation: Evaluation) => {
        const statusMap: Record<string, { label: string; color: string }> = {
          pending: { label: '대기', color: 'var(--fnguide-gray-500)' },
          processing: { label: '처리중', color: 'var(--fnguide-secondary)' },
          completed: { label: '완료', color: 'var(--fnguide-primary)' },
          failed: { label: '실패', color: '#dc2626' },
        }
        const status = statusMap[evaluation.status] || { label: evaluation.status, color: 'var(--fnguide-gray-500)' }
        return <span style={{ color: status.color, fontWeight: 500 }}>{status.label}</span>
      }
    },
    { 
      key: 'created_at', 
      label: '생성일',
      render: (evaluation: Evaluation) => new Date(evaluation.created_at).toLocaleDateString('ko-KR')
    },
    { 
      key: 'actions', 
      label: '작업',
      render: (evaluation: Evaluation) => (
        <Link href={`/evaluations/${evaluation.id}`}>
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
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">평가 관리</h1>
        <p className="fnguide-page-subtitle">평가 목록 및 결과 조회</p>
      </div>

      <Card>
        <Table
          columns={columns}
          data={evaluations}
          keyExtractor={(item) => item.id}
        />
        
        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ color: 'var(--fnguide-gray-500)' }}>
            전체 {total}건 중 {skip + 1}-{Math.min(skip + limit, total)}건 표시
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSkip(Math.max(0, skip - limit))}
              disabled={skip === 0}
            >
              이전
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSkip(skip + limit)}
              disabled={skip + limit >= total}
            >
              다음
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}


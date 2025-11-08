'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Report {
  id: string
  title: string
  analyst_id: string
  company_id?: string
  publication_date: string
  status: string
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const limit = 20

  useEffect(() => {
    loadReports()
  }, [skip])

  const loadReports = async () => {
    try {
      const res = await api.get('/api/reports', {
        params: { skip, limit }
      })
      setReports(res.data.reports || [])
      setTotal(res.data.total || 0)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const columns = [
    { key: 'title', label: '제목' },
    { 
      key: 'publication_date', 
      label: '발간일',
      render: (report: Report) => new Date(report.publication_date).toLocaleDateString('ko-KR')
    },
    { 
      key: 'status', 
      label: '상태',
      render: (report: Report) => {
        const statusMap: Record<string, { label: string; color: string }> = {
          pending: { label: '대기', color: 'var(--fnguide-gray-500)' },
          processing: { label: '처리중', color: 'var(--fnguide-secondary)' },
          completed: { label: '완료', color: 'var(--fnguide-primary)' },
          failed: { label: '실패', color: '#dc2626' },
        }
        const status = statusMap[report.status] || { label: report.status, color: 'var(--fnguide-gray-500)' }
        return <span style={{ color: status.color, fontWeight: 500 }}>{status.label}</span>
      }
    },
    { 
      key: 'actions', 
      label: '작업',
      render: (report: Report) => (
        <Link href={`/reports/${report.id}`}>
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
          <h1 className="fnguide-page-title">리포트 관리</h1>
          <p className="fnguide-page-subtitle">리포트 목록 및 관리</p>
        </div>
        <Link href="/reports/upload">
          <Button variant="primary">리포트 업로드</Button>
        </Link>
      </div>

      <Card>
        <Table
          columns={columns}
          data={reports}
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


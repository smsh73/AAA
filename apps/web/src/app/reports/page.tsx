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

interface GroupedPeriod {
  period: string
  analysts: Array<{
    analyst_id: string
    analyst_name: string
    analyst_firm: string
    reports: Array<{
      id: string
      title: string
      publication_date: string
      status: string
      company_id?: string
    }>
  }>
  total_reports: number
}

export default function ReportsPage() {
  const [groupedData, setGroupedData] = useState<GroupedPeriod[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'grouped' | 'list'>('grouped')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')

  useEffect(() => {
    if (viewMode === 'grouped') {
      loadGroupedReports()
    } else {
      loadReports()
    }
  }, [viewMode, selectedPeriod])

  const [reports, setReports] = useState<Report[]>([])
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const limit = 20

  const loadGroupedReports = async () => {
    try {
      const params: any = {}
      if (selectedPeriod) {
        params.period = selectedPeriod
      }
      const res = await api.get('/api/reports/grouped', { params })
      setGroupedData(res.data.periods || [])
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

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
          <p className="fnguide-page-subtitle">기간별 리포트 목록 및 관리</p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          >
            <option value="">전체 기간</option>
            {Array.from(new Set(groupedData.map(p => p.period))).map(period => (
              <option key={period} value={period}>{period}</option>
            ))}
          </select>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setViewMode(viewMode === 'grouped' ? 'list' : 'grouped')}
          >
            {viewMode === 'grouped' ? '목록 보기' : '계층 보기'}
          </Button>
          <Link href="/reports/upload">
            <Button variant="primary">리포트 업로드</Button>
          </Link>
        </div>
      </div>

      {viewMode === 'grouped' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {groupedData.map((periodData) => (
            <Card key={periodData.period}>
              <div style={{ marginBottom: '16px', paddingBottom: '12px', borderBottom: '2px solid var(--fnguide-gray-200)' }}>
                <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
                  {periodData.period}
                </h2>
                <p style={{ margin: '4px 0 0 0', color: 'var(--fnguide-gray-500)', fontSize: '14px' }}>
                  총 {periodData.total_reports}개의 리포트
                </p>
              </div>

              {periodData.analysts.map((analyst) => (
                <div key={analyst.analyst_id} style={{ marginBottom: '24px', paddingLeft: '16px', borderLeft: '3px solid var(--fnguide-primary)' }}>
                  <div style={{ marginBottom: '12px' }}>
                    <Link href={`/analysts/${analyst.analyst_id}`} style={{ textDecoration: 'none' }}>
                      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--fnguide-primary)' }}>
                        {analyst.analyst_name} ({analyst.analyst_firm})
                      </h3>
                    </Link>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {analyst.reports.map((report) => (
                      <div key={report.id} style={{ 
                        padding: '12px', 
                        backgroundColor: 'var(--fnguide-gray-50)', 
                        borderRadius: '4px',
                        border: '1px solid var(--fnguide-gray-200)'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ flex: 1 }}>
                            <Link href={`/reports/${report.id}`} style={{ textDecoration: 'none', color: 'var(--fnguide-primary)' }}>
                              <strong>{report.title}</strong>
                            </Link>
                            {report.publication_date && (
                              <div style={{ marginTop: '4px', fontSize: '14px', color: 'var(--fnguide-gray-500)' }}>
                                발간일: {new Date(report.publication_date).toLocaleDateString('ko-KR')}
                              </div>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              backgroundColor: report.status === 'completed' ? 'var(--fnguide-success)' : 
                                             report.status === 'processing' ? 'var(--fnguide-secondary)' : 
                                             report.status === 'failed' ? '#dc2626' : 'var(--fnguide-gray-400)',
                              color: 'white'
                            }}>
                              {report.status === 'completed' ? '완료' : 
                               report.status === 'processing' ? '처리중' : 
                               report.status === 'failed' ? '실패' : '대기'}
                            </span>
                            <Link href={`/reports/${report.id}`}>
                              <Button variant="secondary" size="sm">상세</Button>
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {periodData.analysts.length === 0 && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--fnguide-gray-400)' }}>
                  이 기간에 리포트가 없습니다.
                </div>
              )}
            </Card>
          ))}

          {groupedData.length === 0 && (
            <Card>
              <div style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
                리포트 데이터가 없습니다.
              </div>
            </Card>
          )}
        </div>
      ) : (
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
      )}
    </div>
  )
}


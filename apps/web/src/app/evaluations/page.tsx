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

interface GroupedPeriod {
  period: string
  analysts: Array<{
    analyst_id: string
    analyst_name: string
    analyst_firm: string
    reports: Array<{
      report_id: string
      report_title: string
      evaluations: Array<{
        id: string
        final_score?: number
        status: string
        created_at: string
      }>
    }>
  }>
  total_evaluations: number
}

export default function EvaluationsPage() {
  const [groupedData, setGroupedData] = useState<GroupedPeriod[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'grouped' | 'list'>('grouped')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')

  useEffect(() => {
    if (viewMode === 'grouped') {
      loadGroupedEvaluations()
    } else {
      loadEvaluations()
    }
  }, [viewMode, selectedPeriod])

  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const limit = 20

  const loadGroupedEvaluations = async () => {
    try {
      const params: any = {}
      if (selectedPeriod) {
        params.period = selectedPeriod
      }
      const res = await api.get('/api/evaluations/grouped', { params })
      setGroupedData(res.data.periods || [])
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

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
      <div className="fnguide-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="fnguide-page-title">평가 관리</h1>
          <p className="fnguide-page-subtitle">기간별 평가 목록 및 결과 조회</p>
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
                  총 {periodData.total_evaluations}건의 평가
                </p>
              </div>

              {periodData.analysts.map((analyst) => (
                <div key={analyst.analyst_id} style={{ marginBottom: '24px', paddingLeft: '16px', borderLeft: '3px solid var(--fnguide-primary)' }}>
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                      {analyst.analyst_name} ({analyst.analyst_firm})
                    </h3>
                  </div>

                  {analyst.reports.map((report) => (
                    <div key={report.report_id} style={{ marginBottom: '16px', paddingLeft: '16px', marginLeft: '16px', borderLeft: '2px solid var(--fnguide-gray-300)' }}>
                      <div style={{ marginBottom: '8px' }}>
                        <Link href={`/reports/${report.report_id}`} style={{ textDecoration: 'none', color: 'var(--fnguide-primary)' }}>
                          <strong>{report.report_title}</strong>
                        </Link>
                      </div>

                      {report.evaluations.map((evaluation) => (
                        <div key={evaluation.id} style={{ marginBottom: '8px', padding: '8px', backgroundColor: 'var(--fnguide-gray-50)', borderRadius: '4px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <Link href={`/evaluations/${evaluation.id}`} style={{ textDecoration: 'none', color: 'var(--fnguide-primary)' }}>
                                평가 #{evaluation.id.substring(0, 8)}
                              </Link>
                              {evaluation.final_score !== null && evaluation.final_score !== undefined && (
                                <span style={{ marginLeft: '12px', fontWeight: 600 }}>
                                  점수: {evaluation.final_score.toFixed(2)}점
                                </span>
                              )}
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              <span style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                backgroundColor: evaluation.status === 'completed' ? 'var(--fnguide-success)' : 
                                               evaluation.status === 'processing' ? 'var(--fnguide-secondary)' : 
                                               evaluation.status === 'failed' ? '#dc2626' : 'var(--fnguide-gray-400)',
                                color: 'white'
                              }}>
                                {evaluation.status === 'completed' ? '완료' : 
                                 evaluation.status === 'processing' ? '처리중' : 
                                 evaluation.status === 'failed' ? '실패' : '대기'}
                              </span>
                              <Link href={`/evaluations/${evaluation.id}`}>
                                <Button variant="secondary" size="sm">상세</Button>
                              </Link>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </Card>
          ))}

          {groupedData.length === 0 && (
            <Card>
              <div style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
                평가 데이터가 없습니다.
              </div>
            </Card>
          )}
        </div>
      ) : (
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
      )}
    </div>
  )
}


'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Table from '@/components/UI/Table'
import Button from '@/components/UI/Button'

interface ApiLog {
  id: string
  method: string
  path: string
  endpoint: string
  status_code: number
  user_id?: string
  client_ip?: string
  request_time?: number
  error_code?: string
  error_message?: string
  error_type?: string
  function_calls?: any
  service_calls?: any
  external_api_calls?: any
  request_id?: string
  session_id?: string
  created_at: string
}

interface LogStats {
  total: number
  success: number
  errors: number
  error_rate: number
  avg_request_time: number
  status_code_stats: Array<{ status_code: number; count: number }>
  method_stats: Array<{ method: string; count: number }>
  top_paths: Array<{ path: string; count: number }>
}

export default function LogsPage() {
  const [logs, setLogs] = useState<ApiLog[]>([])
  const [stats, setStats] = useState<LogStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLog, setSelectedLog] = useState<ApiLog | null>(null)
  const [filters, setFilters] = useState({
    method: '',
    path: '',
    status_code: '',
    user_id: '',
    error_only: false,
  })
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 100,
    total: 0,
  })

  useEffect(() => {
    loadLogs()
    loadStats()
  }, [filters, pagination.skip])

  const loadLogs = async () => {
    try {
      const params = new URLSearchParams({
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString(),
        ...(filters.method && { method: filters.method }),
        ...(filters.path && { path: filters.path }),
        ...(filters.status_code && { status_code: filters.status_code }),
        ...(filters.user_id && { user_id: filters.user_id }),
        ...(filters.error_only && { error_only: 'true' }),
      })

      const res = await api.get(`/api/logs?${params}`)
      setLogs(res.data.logs || [])
      setPagination({ ...pagination, total: res.data.total || 0 })
      setLoading(false)
    } catch (err) {
      console.error('로그 로드 실패:', err)
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await api.get('/api/logs/stats')
      setStats(res.data)
    } catch (err) {
      console.error('통계 로드 실패:', err)
    }
  }

  const handleDownload = async (format: 'json' | 'csv') => {
    try {
      const params = new URLSearchParams({
        limit: '10000',
        ...(filters.method && { method: filters.method }),
        ...(filters.path && { path: filters.path }),
        ...(filters.status_code && { status_code: filters.status_code }),
        ...(filters.user_id && { user_id: filters.user_id }),
        ...(filters.error_only && { error_only: 'true' }),
      })

      const url = `/api/logs/download/${format}?${params}`
      const res = await api.get(url, { responseType: 'blob' })
      
      const blob = new Blob([res.data], {
        type: format === 'json' ? 'application/json' : 'text/csv',
      })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `api_logs_${new Date().toISOString().slice(0, 10)}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error('다운로드 실패:', err)
      alert('다운로드 실패')
    }
  }

  const handleViewDetail = async (logId: string) => {
    try {
      const res = await api.get(`/api/logs/${logId}`)
      setSelectedLog(res.data)
    } catch (err) {
      console.error('상세 로그 로드 실패:', err)
    }
  }

  const getStatusColor = (statusCode: number) => {
    if (statusCode >= 500) return '#dc2626'
    if (statusCode >= 400) return '#f59e0b'
    if (statusCode >= 300) return '#3b82f6'
    return '#10b981'
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

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">로그 관리자</h1>
        <p className="fnguide-page-subtitle">API 호출 로그 조회 및 다운로드</p>
      </div>

      {/* 통계 */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <Card>
            <div style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>{stats.total.toLocaleString()}</div>
            <div style={{ color: 'var(--fnguide-gray-600)' }}>전체 요청</div>
          </Card>
          <Card>
            <div style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px', color: '#10b981' }}>
              {stats.success.toLocaleString()}
            </div>
            <div style={{ color: 'var(--fnguide-gray-600)' }}>성공</div>
          </Card>
          <Card>
            <div style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px', color: '#dc2626' }}>
              {stats.errors.toLocaleString()}
            </div>
            <div style={{ color: 'var(--fnguide-gray-600)' }}>에러</div>
          </Card>
          <Card>
            <div style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
              {stats.error_rate.toFixed(2)}%
            </div>
            <div style={{ color: 'var(--fnguide-gray-600)' }}>에러율</div>
          </Card>
          <Card>
            <div style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
              {(stats.avg_request_time * 1000).toFixed(0)}ms
            </div>
            <div style={{ color: 'var(--fnguide-gray-600)' }}>평균 응답 시간</div>
          </Card>
        </div>
      )}

      {/* 필터 */}
      <Card>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>필터</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Method</label>
            <select
              value={filters.method}
              onChange={(e) => setFilters({ ...filters, method: e.target.value })}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px',
              }}
            >
              <option value="">전체</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Path</label>
            <input
              type="text"
              value={filters.path}
              onChange={(e) => setFilters({ ...filters, path: e.target.value })}
              placeholder="경로 검색"
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Status Code</label>
            <input
              type="number"
              value={filters.status_code}
              onChange={(e) => setFilters({ ...filters, status_code: e.target.value })}
              placeholder="예: 200, 404, 500"
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>User ID</label>
            <input
              type="text"
              value={filters.user_id}
              onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
              placeholder="사용자 ID"
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={filters.error_only}
                onChange={(e) => setFilters({ ...filters, error_only: e.target.checked })}
              />
              <span>에러만 보기</span>
            </label>
          </div>
        </div>
        <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
          <Button variant="primary" onClick={loadLogs}>
            검색
          </Button>
          <Button variant="secondary" onClick={() => {
            setFilters({ method: '', path: '', status_code: '', user_id: '', error_only: false })
            setPagination({ ...pagination, skip: 0 })
          }}>
            초기화
          </Button>
          <Button variant="secondary" onClick={() => handleDownload('json')}>
            JSON 다운로드
          </Button>
          <Button variant="secondary" onClick={() => handleDownload('csv')}>
            CSV 다운로드
          </Button>
        </div>
      </Card>

      {/* 로그 목록 */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
            로그 목록 ({pagination.total.toLocaleString()}개)
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPagination({ ...pagination, skip: Math.max(0, pagination.skip - pagination.limit) })}
              disabled={pagination.skip === 0}
            >
              이전
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPagination({ ...pagination, skip: pagination.skip + pagination.limit })}
              disabled={pagination.skip + pagination.limit >= pagination.total}
            >
              다음
            </Button>
          </div>
        </div>

        {logs.length > 0 ? (
          <Table
            columns={[
              {
                key: 'method',
                label: 'Method',
                render: (log: ApiLog) => (
                  <span style={{ fontWeight: 600, color: '#3b82f6' }}>{log.method}</span>
                ),
              },
              {
                key: 'path',
                label: 'Path',
                render: (log: ApiLog) => (
                  <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{log.path}</span>
                ),
              },
              {
                key: 'status_code',
                label: 'Status',
                render: (log: ApiLog) => (
                  <span style={{ color: getStatusColor(log.status_code), fontWeight: 600 }}>
                    {log.status_code}
                  </span>
                ),
              },
              {
                key: 'user_id',
                label: 'User ID',
                render: (log: ApiLog) => log.user_id || '-',
              },
              {
                key: 'client_ip',
                label: 'IP',
                render: (log: ApiLog) => log.client_ip || '-',
              },
              {
                key: 'request_time',
                label: 'Time',
                render: (log: ApiLog) => log.request_time ? `${(log.request_time * 1000).toFixed(0)}ms` : '-',
              },
              {
                key: 'error_message',
                label: 'Error',
                render: (log: ApiLog) => log.error_message ? (
                  <span style={{ color: '#dc2626', fontSize: '12px' }}>
                    {log.error_message.substring(0, 50)}...
                  </span>
                ) : '-',
              },
              {
                key: 'created_at',
                label: 'Created',
                render: (log: ApiLog) => new Date(log.created_at).toLocaleString('ko-KR'),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (log: ApiLog) => (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleViewDetail(log.id)}
                  >
                    상세
                  </Button>
                ),
              },
            ]}
            data={logs}
            keyExtractor={(item) => item.id}
          />
        ) : (
          <p style={{ color: 'var(--fnguide-gray-400)', textAlign: 'center', padding: '48px' }}>
            로그가 없습니다.
          </p>
        )}
      </Card>

      {/* 상세 로그 모달 */}
      {selectedLog && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedLog(null)}
        >
          <Card
            style={{
              maxWidth: '90%',
              maxHeight: '90%',
              overflow: 'auto',
              width: '800px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>로그 상세</h2>
              <Button variant="secondary" size="sm" onClick={() => setSelectedLog(null)}>
                닫기
              </Button>
            </div>
            <pre style={{
              backgroundColor: '#1e1e1e',
              color: '#d4d4d4',
              padding: '16px',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px',
              fontFamily: 'monospace',
            }}>
              {JSON.stringify(selectedLog, null, 2)}
            </pre>
          </Card>
        </div>
      )}
    </div>
  )
}


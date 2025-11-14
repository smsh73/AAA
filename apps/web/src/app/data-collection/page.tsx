'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Table from '@/components/UI/Table'
import Button from '@/components/UI/Button'

interface Analyst {
  id: string
  name: string
  firm: string
}

interface CollectionJob {
  collection_job_id: string
  status: string
  progress: Record<string, { total: number; completed: number; failed: number }>
  overall_progress: number | string
  started_at?: string
  completed_at?: string
  error_message?: string
}

interface CollectionLog {
  id: string
  analyst_id: string
  company_id?: string
  collection_job_id?: string
  collection_type: string
  status: string
  collected_data?: any
  error_message?: string
  log_message?: string
  collection_time?: number
  created_at: string
  updated_at: string
}

export default function DataCollectionPage() {
  const [analysts, setAnalysts] = useState<Analyst[]>([])
  const [selectedAnalyst, setSelectedAnalyst] = useState<string>('')
  const [collectionTypes, setCollectionTypes] = useState<string[]>([])
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [activeJobs, setActiveJobs] = useState<CollectionJob[]>([])
  const [logs, setLogs] = useState<CollectionLog[]>([])
  const [realtimeLogs, setRealtimeLogs] = useState<CollectionLog[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showRealtimeLogs, setShowRealtimeLogs] = useState(false)
  const [showBulkForm, setShowBulkForm] = useState(false)
  const [bulkSubmitting, setBulkSubmitting] = useState(false)

  useEffect(() => {
    loadAnalysts()
    loadLogs()
    // 활성 작업 상태 주기적으로 업데이트 (30초마다)
    const interval = setInterval(() => {
      loadActiveJobs()
      if (selectedJobId && showRealtimeLogs) {
        loadRealtimeLogs()
      }
    }, 3000) // 3초마다 업데이트
    return () => clearInterval(interval)
  }, [selectedJobId, showRealtimeLogs])

  const loadAnalysts = async () => {
    try {
      const res = await api.get('/api/analysts')
      setAnalysts(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const loadActiveJobs = async () => {
    try {
      // 최근 로그에서 활성 작업 ID 추출
      const recentLogs = await api.get('/api/data-collection/logs?limit=50')
      const jobIds = new Set<string>()
      recentLogs.data.forEach((log: CollectionLog) => {
        if (log.collection_job_id) {
          jobIds.add(log.collection_job_id)
        }
      })

      // 각 작업의 상태 조회
      const jobStatuses = await Promise.all(
        Array.from(jobIds).map(async (jobId) => {
          try {
            const res = await api.get(`/api/data-collection/${jobId}/status`)
            return res.data
          } catch (err) {
            return null
          }
        })
      )

      setActiveJobs(jobStatuses.filter((job) => job && job.status !== 'completed' && job.status !== 'failed'))
    } catch (err) {
      console.error('활성 작업 로드 실패:', err)
    }
  }

  const loadLogs = async () => {
    try {
      const res = await api.get('/api/data-collection/logs?limit=100')
      setLogs(res.data)
      loadActiveJobs()
    } catch (err) {
      console.error('로그 로드 실패:', err)
    }
  }

  const loadRealtimeLogs = async () => {
    if (!selectedJobId) return
    
    try {
      const lastLogId = realtimeLogs.length > 0 ? realtimeLogs[realtimeLogs.length - 1].id : undefined
      const url = `/api/data-collection/logs/realtime?collection_job_id=${selectedJobId}${lastLogId ? `&last_log_id=${lastLogId}` : ''}`
      const res = await api.get(url)
      if (res.data && res.data.length > 0) {
        setRealtimeLogs([...realtimeLogs, ...res.data])
      }
    } catch (err) {
      console.error('실시간 로그 로드 실패:', err)
    }
  }

  const handleShowRealtimeLogs = (jobId: string) => {
    setSelectedJobId(jobId)
    setShowRealtimeLogs(true)
    setRealtimeLogs([])
    loadRealtimeLogs()
  }

  const handleStartCollection = async () => {
    if (!selectedAnalyst || collectionTypes.length === 0 || !startDate || !endDate) {
      alert('모든 필드를 입력해주세요.')
      return
    }

    setSubmitting(true)
    try {
      const res = await api.post('/api/data-collection/start', {
        analyst_id: selectedAnalyst,
        collection_types: collectionTypes,
        start_date: startDate,
        end_date: endDate,
      })

      alert(`데이터 수집이 시작되었습니다. 작업 ID: ${res.data.collection_job_id}`)
      setShowForm(false)
      setSelectedAnalyst('')
      setCollectionTypes([])
      setStartDate('')
      setEndDate('')
      
      // 로그 새로고침
      setTimeout(() => {
        loadLogs()
      }, 2000)
    } catch (err: any) {
      alert(`데이터 수집 시작 실패: ${err.response?.data?.detail || err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleStartBulkCollection = async () => {
    if (collectionTypes.length === 0 || !startDate || !endDate) {
      alert('수집 타입, 시작일, 종료일을 모두 입력해주세요.')
      return
    }

    if (!confirm(`전체 애널리스트(${analysts.length}명)에 대해 데이터 수집을 시작하시겠습니까? 이 작업은 시간이 오래 걸릴 수 있습니다.`)) {
      return
    }

    setBulkSubmitting(true)
    try {
      const res = await api.post('/api/data-collection/bulk-start', {
        collection_types: collectionTypes,
        start_date: startDate,
        end_date: endDate,
        analyst_ids: null, // 전체 애널리스트
      })

      alert(
        `전체 일괄 수집이 시작되었습니다.\n` +
        `총 애널리스트: ${res.data.total_analysts}명\n` +
        `시작된 작업: ${res.data.started_jobs}개\n` +
        `실패: ${res.data.failed_analysts.length}개`
      )
      
      if (res.data.failed_analysts.length > 0) {
        console.error('실패한 애널리스트:', res.data.failed_analysts)
      }
      
      setShowBulkForm(false)
      setCollectionTypes([])
      setStartDate('')
      setEndDate('')
      
      // 로그 새로고침
      setTimeout(() => {
        loadLogs()
      }, 2000)
    } catch (err: any) {
      alert(`전체 일괄 수집 시작 실패: ${err.response?.data?.detail || err.message}`)
    } finally {
      setBulkSubmitting(false)
    }
  }

  const handleCollectionTypeChange = (type: string, checked: boolean) => {
    if (checked) {
      setCollectionTypes([...collectionTypes, type])
    } else {
      setCollectionTypes(collectionTypes.filter((t) => t !== type))
    }
  }

  const collectionTypeLabels: Record<string, string> = {
    target_price: '목표주가',
    performance: '실적',
    sns: 'SNS',
    media: '언론',
  }

  const statusLabels: Record<string, string> = {
    pending: '대기',
    running: '진행중',
    completed: '완료',
    failed: '실패',
    success: '성공',
    partial: '부분성공',
  }

  const statusColors: Record<string, string> = {
    pending: 'var(--fnguide-gray-500)',
    running: 'var(--fnguide-secondary)',
    completed: 'var(--fnguide-primary)',
    failed: '#dc2626',
    success: 'var(--fnguide-primary)',
    partial: '#f59e0b',
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
        <h1 className="fnguide-page-title">데이터 수집 관리</h1>
        <p className="fnguide-page-subtitle">데이터 수집 작업 시작 및 모니터링</p>
      </div>

      {/* 데이터 수집 시작 폼 */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>새 데이터 수집 작업</h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant={showBulkForm ? 'secondary' : 'primary'}
              onClick={() => {
                setShowBulkForm(!showBulkForm)
                setShowForm(false)
              }}
            >
              {showBulkForm ? '닫기' : '전체 일괄 수집'}
            </Button>
            <Button
              variant={showForm ? 'secondary' : 'primary'}
              onClick={() => {
                setShowForm(!showForm)
                setShowBulkForm(false)
              }}
            >
              {showForm ? '닫기' : '개별 수집'}
            </Button>
          </div>
        </div>

        {showForm && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                애널리스트 선택 *
              </label>
              <select
                value={selectedAnalyst}
                onChange={(e) => setSelectedAnalyst(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid var(--fnguide-gray-300)',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              >
                <option value="">선택하세요</option>
                {analysts.map((analyst) => (
                  <option key={analyst.id} value={analyst.id}>
                    {analyst.name} ({analyst.firm})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                수집 타입 선택 *
              </label>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                {Object.entries(collectionTypeLabels).map(([type, label]) => (
                  <label key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={collectionTypes.includes(type)}
                      onChange={(e) => handleCollectionTypeChange(type, e.target.checked)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  시작일 *
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--fnguide-gray-300)',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  종료일 *
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--fnguide-gray-300)',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleStartCollection}
              disabled={submitting}
              style={{ alignSelf: 'flex-start' }}
            >
              {submitting ? '시작 중...' : '수집 시작'}
            </Button>
          </div>
        )}

        {/* 전체 일괄 수집 폼 */}
        {showBulkForm && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '16px', borderTop: '1px solid var(--fnguide-gray-200)', marginTop: '16px' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--fnguide-gray-50)', borderRadius: '4px', marginBottom: '8px' }}>
              <strong>전체 일괄 수집</strong>
              <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: 'var(--fnguide-gray-600)' }}>
                등록된 모든 애널리스트({analysts.length}명)에 대해 데이터 수집을 시작합니다. 이 작업은 시간이 오래 걸릴 수 있습니다.
              </p>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                수집 타입 선택 *
              </label>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                {Object.entries(collectionTypeLabels).map(([type, label]) => (
                  <label key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={collectionTypes.includes(type)}
                      onChange={(e) => handleCollectionTypeChange(type, e.target.checked)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  시작일 *
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--fnguide-gray-300)',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  종료일 *
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--fnguide-gray-300)',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleStartBulkCollection}
              disabled={bulkSubmitting}
              style={{ alignSelf: 'flex-start', backgroundColor: bulkSubmitting ? 'var(--fnguide-gray-400)' : '#dc2626' }}
            >
              {bulkSubmitting ? '전체 수집 시작 중...' : `전체 일괄 수집 시작 (${analysts.length}명)`}
            </Button>
          </div>
        )}
      </Card>

      {/* 진행 중인 작업 */}
      {activeJobs.length > 0 && (
        <Card>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>진행 중인 작업</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeJobs.map((job) => (
              <div
                key={job.collection_job_id}
                style={{
                  padding: '16px',
                  border: '1px solid var(--fnguide-gray-300)',
                  borderRadius: '8px',
                  backgroundColor: 'var(--fnguide-gray-50)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div>
                    <strong>작업 ID:</strong> {job.collection_job_id.substring(0, 8)}...
                  </div>
                  <span
                    style={{
                      padding: '4px 12px',
                      borderRadius: '4px',
                      backgroundColor: statusColors[job.status] || 'var(--fnguide-gray-500)',
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: 500,
                    }}
                  >
                    {statusLabels[job.status] || job.status}
                  </span>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>전체 진행률:</strong> {typeof job.overall_progress === 'number' ? job.overall_progress.toFixed(1) : parseFloat(String(job.overall_progress || 0)).toFixed(1)}%
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>상세 진행률:</strong>
                  <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {Object.entries(job.progress).map(([type, progress]) => (
                      <div key={type} style={{ fontSize: '14px' }}>
                        {collectionTypeLabels[type] || type}: {progress.completed}/{progress.total} 완료
                        {progress.failed > 0 && <span style={{ color: '#dc2626' }}> ({progress.failed} 실패)</span>}
                      </div>
                    ))}
                  </div>
                </div>
                {job.started_at && (
                  <div style={{ fontSize: '12px', color: 'var(--fnguide-gray-600)' }}>
                    시작: {new Date(job.started_at).toLocaleString('ko-KR')}
                  </div>
                )}
                {job.error_message && (
                  <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fee2e2', borderRadius: '4px', fontSize: '14px', color: '#dc2626' }}>
                    <strong>오류:</strong> {job.error_message}
                  </div>
                )}
                <div style={{ marginTop: '12px' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleShowRealtimeLogs(job.collection_job_id)}
                  >
                    실시간 로그 보기
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 실시간 로그 모니터링 */}
      {showRealtimeLogs && selectedJobId && (
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>실시간 로그 모니터링</h2>
            <Button variant="secondary" size="sm" onClick={() => {
              setShowRealtimeLogs(false)
              setSelectedJobId('')
              setRealtimeLogs([])
            }}>
              닫기
            </Button>
          </div>
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
            padding: '16px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '12px'
          }}>
            {realtimeLogs.length === 0 ? (
              <div style={{ color: '#888', textAlign: 'center', padding: '24px' }}>
                로그를 기다리는 중...
              </div>
            ) : (
              realtimeLogs.map((log, index) => (
                <div key={log.id || index} style={{ marginBottom: '8px', paddingBottom: '8px', borderBottom: '1px solid #333' }}>
                  <div style={{ color: '#4ec9b0', marginBottom: '4px' }}>
                    [{new Date(log.created_at).toLocaleTimeString('ko-KR')}] {log.collection_type}
                  </div>
                  {log.log_message && (
                    <div style={{ color: '#d4d4d4', marginLeft: '16px' }}>
                      {log.log_message}
                    </div>
                  )}
                  {log.error_message && (
                    <div style={{ color: '#f48771', marginLeft: '16px' }}>
                      오류: {log.error_message}
                    </div>
                  )}
                  {log.status && (
                    <div style={{ color: log.status === 'success' ? '#4ec9b0' : log.status === 'failed' ? '#f48771' : '#d4d4d4', marginLeft: '16px' }}>
                      상태: {statusLabels[log.status] || log.status}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* 수집 로그 */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>수집 로그</h2>
          <Button variant="secondary" size="sm" onClick={loadLogs}>
            새로고침
          </Button>
        </div>

        {logs.length > 0 ? (
          <Table
            columns={[
              {
                key: 'collection_type',
                label: '수집 타입',
                render: (log: CollectionLog) => collectionTypeLabels[log.collection_type] || log.collection_type,
              },
              {
                key: 'status',
                label: '상태',
                render: (log: CollectionLog) => {
                  const status = statusLabels[log.status] || log.status
                  const color = statusColors[log.status] || 'var(--fnguide-gray-500)'
                  return <span style={{ color, fontWeight: 500 }}>{status}</span>
                },
              },
              {
                key: 'collection_time',
                label: '소요 시간',
                render: (log: CollectionLog) => log.collection_time ? `${log.collection_time.toFixed(2)}초` : '-',
              },
              {
                key: 'created_at',
                label: '생성일',
                render: (log: CollectionLog) => new Date(log.created_at).toLocaleString('ko-KR'),
              },
              {
                key: 'log_message',
                label: '로그 메시지',
                render: (log: CollectionLog) => log.log_message ? (
                  <span style={{ fontSize: '12px' }}>{log.log_message.substring(0, 100)}</span>
                ) : '-',
              },
              {
                key: 'error_message',
                label: '오류',
                render: (log: CollectionLog) => log.error_message ? (
                  <span style={{ color: '#dc2626', fontSize: '12px' }}>{log.error_message.substring(0, 50)}...</span>
                ) : '-',
              },
            ]}
            data={logs}
            keyExtractor={(item) => item.id}
          />
        ) : (
          <p style={{ color: 'var(--fnguide-gray-400)', textAlign: 'center', padding: '48px' }}>
            데이터 수집 로그가 없습니다.
          </p>
        )}
      </Card>
    </div>
  )
}

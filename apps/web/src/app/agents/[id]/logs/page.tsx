'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'

export default function AgentLogsPage() {
  const params = useParams()
  const agentId = params.id as string
  
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (agentId) {
      loadLogs()
    }
  }, [agentId])

  const loadLogs = async () => {
    try {
      // 실제 로그 API가 구현되면 여기에 연결
      // 현재는 데이터 수집 로그를 예시로 사용
      const res = await api.get('/api/data-collection/logs')
      setLogs(res.data || [])
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

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">{agentId.replace('_', ' ').toUpperCase()} 로그</h1>
        <p className="fnguide-page-subtitle">에이전트 실행 로그 및 상태</p>
      </div>

      <Card>
        {logs.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {logs.map((log: any, index: number) => (
              <div 
                key={index}
                style={{ 
                  padding: '16px', 
                  border: '1px solid var(--fnguide-gray-200)', 
                  borderRadius: '4px',
                  backgroundColor: log.status === 'success' ? 'var(--fnguide-gray-50)' : 'white'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong>{log.collection_type || 'Unknown'}</strong>
                  <span style={{ 
                    color: log.status === 'success' ? 'var(--fnguide-success)' : 'var(--fnguide-error)',
                    fontSize: '14px'
                  }}>
                    {log.status || 'unknown'}
                  </span>
                </div>
                {log.created_at && (
                  <div style={{ fontSize: '12px', color: 'var(--fnguide-gray-500)', marginBottom: '8px' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                )}
                {log.error_message && (
                  <div style={{ color: 'var(--fnguide-error)', fontSize: '14px', marginTop: '8px' }}>
                    {log.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
            로그가 없습니다.
          </div>
        )}
      </Card>
    </div>
  )
}


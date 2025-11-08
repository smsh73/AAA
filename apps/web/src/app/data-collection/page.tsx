'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Table from '@/components/UI/Table'
import Button from '@/components/UI/Button'

interface CollectionLog {
  id: string
  analyst_id: string
  collection_type: string
  status: string
  created_at: string
}

export default function DataCollectionPage() {
  const [logs, setLogs] = useState<CollectionLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: API 연동
    setLogs([])
    setLoading(false)
  }, [])

  const columns = [
    { key: 'collection_type', label: '수집 타입' },
    { 
      key: 'status', 
      label: '상태',
      render: (log: CollectionLog) => {
        const statusMap: Record<string, { label: string; color: string }> = {
          pending: { label: '대기', color: 'var(--fnguide-gray-500)' },
          processing: { label: '처리중', color: 'var(--fnguide-secondary)' },
          success: { label: '완료', color: 'var(--fnguide-primary)' },
          failed: { label: '실패', color: '#dc2626' },
        }
        const status = statusMap[log.status] || { label: log.status, color: 'var(--fnguide-gray-500)' }
        return <span style={{ color: status.color, fontWeight: 500 }}>{status.label}</span>
      }
    },
    { 
      key: 'created_at', 
      label: '생성일',
      render: (log: CollectionLog) => new Date(log.created_at).toLocaleDateString('ko-KR')
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
        <h1 className="fnguide-page-title">데이터 수집 관리</h1>
        <p className="fnguide-page-subtitle">데이터 수집 작업 모니터링</p>
      </div>

      <Card>
        {logs.length > 0 ? (
          <Table
            columns={columns}
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


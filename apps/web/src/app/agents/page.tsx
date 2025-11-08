'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Agent {
  name: string
  status: string
  description: string
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const res = await api.get('/api/agents/status')
      setAgents(res.data.agents || [])
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
        <h1 className="fnguide-page-title">에이전트 콘솔</h1>
        <p className="fnguide-page-subtitle">AI 에이전트 상태 모니터링 및 관리</p>
      </div>

      <div className="fnguide-grid fnguide-grid-3">
        {agents.map((agent) => (
          <Card key={agent.name} title={agent.name.replace('_', ' ').toUpperCase()}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <strong>상태:</strong>{' '}
                <span style={{ 
                  color: agent.status === 'active' ? 'var(--fnguide-success)' : 'var(--fnguide-error)',
                  fontWeight: 600
                }}>
                  {agent.status === 'active' ? '활성' : '비활성'}
                </span>
              </div>
              <div style={{ color: 'var(--fnguide-gray-600)', fontSize: '14px' }}>
                {agent.description}
              </div>
              <div style={{ marginTop: '8px' }}>
                <Link href={`/agents/${agent.name}/logs`}>
                  <Button variant="secondary" size="sm">로그 보기</Button>
                </Link>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}


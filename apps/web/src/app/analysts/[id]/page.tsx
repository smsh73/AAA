'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'

interface AnalystDetail {
  id: string
  name: string
  firm: string
  department?: string
  sector?: string
  experience_years?: number
  email?: string
  profile_url?: string
  bio?: string
}

export default function AnalystDetailPage() {
  const params = useParams()
  const analystId = params.id as string
  
  const [analyst, setAnalyst] = useState<AnalystDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (analystId) {
      loadAnalyst()
    }
  }, [analystId])

  const loadAnalyst = async () => {
    try {
      const res = await api.get(`/api/analysts/${analystId}`)
      setAnalyst(res.data)
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

  if (!analyst) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          애널리스트를 찾을 수 없습니다.
        </div>
      </div>
    )
  }

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">{analyst.name}</h1>
        <p className="fnguide-page-subtitle">{analyst.firm}</p>
      </div>

      <div className="fnguide-grid fnguide-grid-2">
        <Card title="기본 정보">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <strong>증권사:</strong> {analyst.firm}
            </div>
            {analyst.department && (
              <div>
                <strong>부서:</strong> {analyst.department}
              </div>
            )}
            {analyst.sector && (
              <div>
                <strong>섹터:</strong> {analyst.sector}
              </div>
            )}
            {analyst.experience_years && (
              <div>
                <strong>경력:</strong> {analyst.experience_years}년
              </div>
            )}
            {analyst.email && (
              <div>
                <strong>이메일:</strong> {analyst.email}
              </div>
            )}
          </div>
        </Card>

        {analyst.bio && (
          <Card title="소개">
            <p style={{ color: 'var(--fnguide-gray-600)', lineHeight: '1.6' }}>
              {analyst.bio}
            </p>
          </Card>
        )}
      </div>
    </div>
  )
}


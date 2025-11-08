'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Analyst {
  id: string
  name: string
  firm: string
  sector: string
  email?: string
  department?: string
  experience_years?: number
}

export default function AnalystsPage() {
  const [analysts, setAnalysts] = useState<Analyst[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/analysts')
      .then((res) => {
        setAnalysts(res.data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  const columns = [
    { key: 'name', label: '이름' },
    { key: 'firm', label: '증권사' },
    { key: 'department', label: '부서' },
    { key: 'sector', label: '섹터' },
    { key: 'experience_years', label: '경력(년)' },
    { 
      key: 'actions', 
      label: '작업',
      render: (analyst: Analyst) => (
        <Link href={`/analysts/${analyst.id}`}>
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
        <h1 className="fnguide-page-title">애널리스트 관리</h1>
        <p className="fnguide-page-subtitle">애널리스트 목록 및 관리</p>
      </div>

      <Card>
        <Table
          columns={columns}
          data={analysts}
          keyExtractor={(item) => item.id}
        />
      </Card>
    </div>
  )
}


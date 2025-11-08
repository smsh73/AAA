'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Company {
  id: string
  name?: string
  name_kr?: string
  name_en?: string
  ticker?: string
  sector?: string
  industry?: string
  market_cap?: number
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCompanies()
  }, [])

  const loadCompanies = async () => {
    try {
      const res = await api.get('/api/companies')
      setCompanies(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const columns = [
    { 
      key: 'name', 
      label: '기업명',
      render: (company: Company) => company.name_kr || company.name || company.name_en || '이름 없음'
    },
    { key: 'ticker', label: '종목코드' },
    { key: 'sector', label: '섹터' },
    { key: 'industry', label: '산업' },
    { 
      key: 'actions', 
      label: '작업',
      render: (company: Company) => (
        <Link href={`/companies/${company.id}`}>
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
        <h1 className="fnguide-page-title">기업 관리</h1>
        <p className="fnguide-page-subtitle">기업 목록 및 관리</p>
      </div>

      <Card>
        {companies.length > 0 ? (
          <>
            <div style={{ marginBottom: '16px', color: 'var(--fnguide-gray-500)' }}>
              전체 {companies.length}개
            </div>
            <Table
              columns={columns}
              data={companies}
              keyExtractor={(item) => item.id}
            />
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
            등록된 기업이 없습니다.
          </div>
        )}
      </Card>
    </div>
  )
}


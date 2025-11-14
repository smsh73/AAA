'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Link from 'next/link'
import Button from '@/components/UI/Button'

interface CompanyDetail {
  id: string
  name?: string
  name_kr?: string
  name_en?: string
  ticker?: string
  sector?: string
  industry?: string
  market_cap?: number
  fundamentals?: any
}

export default function CompanyDetailPage() {
  const params = useParams()
  const companyId = params.id as string
  
  const [company, setCompany] = useState<CompanyDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [reports, setReports] = useState<any[]>([])
  const [analysts, setAnalysts] = useState<any[]>([])

  useEffect(() => {
    if (companyId) {
      loadCompany()
      loadCompanyReports()
      loadCompanyAnalysts()
    }
  }, [companyId])

  const loadCompany = async () => {
    try {
      const res = await api.get(`/api/companies/${companyId}`)
      setCompany(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const loadCompanyReports = async () => {
    try {
      const res = await api.get(`/api/reports?company_id=${companyId}`)
      setReports(res.data || [])
    } catch (err) {
      console.error(err)
    }
  }

  const loadCompanyAnalysts = async () => {
    try {
      // 이 기업에 대한 리포트를 작성한 애널리스트 목록
      const res = await api.get(`/api/reports?company_id=${companyId}`)
      const reportData = res.data || []
      const analystIds = Array.from(new Set(reportData.map((r: any) => r.analyst_id))) as string[]
      
      if (analystIds.length > 0) {
        const analystPromises = analystIds.map((id: string) => 
          api.get(`/api/analysts/${id}`).catch(() => null)
        )
        const analystResults = await Promise.all(analystPromises)
        setAnalysts(analystResults.filter(r => r !== null).map(r => r.data))
      }
    } catch (err) {
      console.error(err)
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

  if (!company) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          기업을 찾을 수 없습니다.
        </div>
      </div>
    )
  }

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">{company.name_kr || company.name || company.name_en || '이름 없음'}</h1>
        <p className="fnguide-page-subtitle">{company.ticker || '종목코드 없음'}</p>
      </div>

      <div className="fnguide-grid fnguide-grid-2">
        <Card title="기본 정보">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {company.ticker && (
              <div>
                <strong>종목코드:</strong> {company.ticker}
              </div>
            )}
            {company.sector && (
              <div>
                <strong>섹터:</strong> {company.sector}
              </div>
            )}
            {company.industry && (
              <div>
                <strong>산업:</strong> {company.industry}
              </div>
            )}
            {company.market_cap && (
              <div>
                <strong>시가총액:</strong> {company.market_cap.toLocaleString()}원
              </div>
            )}
          </div>
        </Card>

        {company.fundamentals && (
          <Card title="재무정보">
            <div style={{ color: 'var(--fnguide-gray-600)', lineHeight: '1.6' }}>
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {JSON.stringify(company.fundamentals, null, 2)}
              </pre>
            </div>
          </Card>
        )}
      </div>

      {analysts.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <Card title="애널리스트 커버리지">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {analysts.map((analyst: any) => (
              <div key={analyst.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Link href={`/analysts/${analyst.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <strong>{analyst.name}</strong> - {analyst.firm}
                  </Link>
                </div>
                <Link href={`/reports?analyst_id=${analyst.id}&company_id=${companyId}`}>
                  <Button variant="secondary" size="sm">리포트 보기</Button>
                </Link>
              </div>
            ))}
          </div>
          </Card>
        </div>
      )}

      {reports.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <Card title="리포트 목록">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {reports.map((report: any) => (
              <div key={report.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', border: '1px solid var(--fnguide-gray-200)', borderRadius: '4px' }}>
                <div>
                  <Link href={`/reports/${report.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <strong>{report.title || '제목 없음'}</strong>
                  </Link>
                  <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)', marginTop: '4px' }}>
                    {report.report_date && new Date(report.report_date).toLocaleDateString()}
                  </div>
                </div>
                <Link href={`/reports/${report.id}`}>
                  <Button variant="secondary" size="sm">상세</Button>
                </Link>
              </div>
            ))}
          </div>
          </Card>
        </div>
      )}
    </div>
  )
}


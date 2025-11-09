'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'
import Table from '@/components/UI/Table'

interface ReportDetail {
  id: string
  title: string
  analyst_id: string
  company_id?: string
  publication_date: string
  status: string
  file_size?: number
  total_pages?: number
  created_at: string
  extracted_company_name?: string
  predictions_count?: number
}

interface Prediction {
  id: string
  prediction_type: string
  predicted_value: number
  unit?: string
  period?: string
}

export default function ReportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const reportId = params.id as string
  
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (reportId) {
      loadReport()
      loadPredictions()
    }
  }, [reportId])

  const loadReport = async () => {
    try {
      const res = await api.get(`/api/reports/${reportId}`)
      setReport(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const loadPredictions = async () => {
    try {
      const res = await api.get(`/api/reports/${reportId}/predictions`)
      setPredictions(res.data.predictions || [])
    } catch (err) {
      console.error(err)
    }
  }

  const handleStartEvaluation = async () => {
    try {
      const res = await api.post('/api/evaluations/start', {
        report_id: reportId
      })
      alert('평가가 시작되었습니다.')
      router.push(`/evaluations/${res.data.evaluation_id}`)
    } catch (err: any) {
      alert(`평가 시작 실패: ${err.response?.data?.detail || err.message}`)
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

  if (!report) {
    return (
      <div className="fnguide-container">
        <div style={{ textAlign: 'center', padding: '48px' }}>
          리포트를 찾을 수 없습니다.
        </div>
      </div>
    )
  }

  const predictionColumns = [
    { key: 'prediction_type', label: '예측 타입' },
    { key: 'predicted_value', label: '예측 값' },
    { key: 'unit', label: '단위' },
    { key: 'period', label: '기간' },
  ]

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="fnguide-page-title">{report.title}</h1>
          <p className="fnguide-page-subtitle">리포트 상세 정보</p>
        </div>
        <Button variant="primary" onClick={handleStartEvaluation}>
          평가 시작
        </Button>
      </div>

      <div className="fnguide-grid fnguide-grid-2" style={{ marginBottom: '24px' }}>
        <Card title="기본 정보">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <strong>상태:</strong>{' '}
              <span style={{ 
                color: report.status === 'completed' ? 'var(--fnguide-primary)' : 'var(--fnguide-gray-500)'
              }}>
                {report.status}
              </span>
            </div>
            <div>
              <strong>발간일:</strong> {new Date(report.publication_date).toLocaleDateString('ko-KR')}
            </div>
            {report.extracted_company_name && (
              <div>
                <strong>추출된 기업:</strong>{' '}
                <span style={{ color: 'var(--fnguide-primary)' }}>
                  {report.extracted_company_name} (자동 추출)
                </span>
              </div>
            )}
            {report.predictions_count !== undefined && (
              <div>
                <strong>추출된 예측:</strong>{' '}
                <span style={{ color: 'var(--fnguide-primary)' }}>
                  {report.predictions_count}개
                </span>
              </div>
            )}
            {report.file_size && (
              <div>
                <strong>파일 크기:</strong> {(report.file_size / 1024 / 1024).toFixed(2)} MB
              </div>
            )}
            {report.total_pages && (
              <div>
                <strong>총 페이지:</strong> {report.total_pages}페이지
              </div>
            )}
          </div>
        </Card>

        <Card title="예측 정보">
          {predictions.length > 0 ? (
            <Table
              columns={predictionColumns}
              data={predictions}
              keyExtractor={(item) => item.id}
            />
          ) : (
            <p style={{ color: 'var(--fnguide-gray-400)' }}>예측 정보가 없습니다.</p>
          )}
        </Card>
      </div>
    </div>
  )
}


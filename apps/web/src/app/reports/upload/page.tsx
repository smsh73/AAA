'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface Analyst {
  id: string
  name: string
  firm: string
}

interface Company {
  id: string
  name: string
  ticker?: string
}

export default function ReportUploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [analysts, setAnalysts] = useState<Analyst[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [selectedAnalystId, setSelectedAnalystId] = useState<string>('')
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('')
  const [loadingOptions, setLoadingOptions] = useState(true)

  useEffect(() => {
    loadOptions()
  }, [])

  const loadOptions = async () => {
    try {
      const [analystsRes, companiesRes] = await Promise.all([
        api.get('/api/analysts'),
        api.get('/api/companies')
      ])
      setAnalysts(analystsRes.data?.analysts || [])
      setCompanies(companiesRes.data?.companies || [])
    } catch (err) {
      console.error('옵션 로드 실패:', err)
    } finally {
      setLoadingOptions(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', file)
      if (selectedAnalystId) {
        formData.append('analyst_id', selectedAnalystId)
      }
      if (selectedCompanyId) {
        formData.append('company_id', selectedCompanyId)
      }

      const res = await api.post('/api/reports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            setProgress(percentCompleted)
          }
        },
      })

      alert('리포트 업로드가 시작되었습니다.')
      router.push(`/reports/${res.data.report_id}`)
    } catch (err: any) {
      console.error(err)
      alert(`업로드 실패: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">리포트 업로드</h1>
        <p className="fnguide-page-subtitle">PDF 리포트 파일을 업로드하세요</p>
      </div>

      <Card>
        <div className="fnguide-form-group">
          <label className="fnguide-form-label">PDF 파일 선택</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="fnguide-form-input"
            disabled={uploading}
          />
          {file && (
            <p style={{ marginTop: '8px', color: 'var(--fnguide-gray-500)' }}>
              선택된 파일: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        <div className="fnguide-form-group">
          <label className="fnguide-form-label">애널리스트 선택 (선택사항)</label>
          <select
            value={selectedAnalystId}
            onChange={(e) => setSelectedAnalystId(e.target.value)}
            className="fnguide-form-input"
            disabled={uploading || loadingOptions}
          >
            <option value="">선택 안 함</option>
            {analysts.map((analyst) => (
              <option key={analyst.id} value={analyst.id}>
                {analyst.name} ({analyst.firm})
              </option>
            ))}
          </select>
        </div>

        <div className="fnguide-form-group">
          <label className="fnguide-form-label">기업 선택 (선택사항)</label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="fnguide-form-input"
            disabled={uploading || loadingOptions}
          >
            <option value="">선택 안 함</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name} {company.ticker && `(${company.ticker})`}
              </option>
            ))}
          </select>
        </div>

        {uploading && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>업로드 진행 중...</span>
              <span>{progress}%</span>
            </div>
            <div style={{ 
              width: '100%', 
              height: '8px', 
              backgroundColor: 'var(--fnguide-gray-200)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: 'var(--fnguide-primary)',
                transition: 'width 0.3s'
              }} />
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            업로드
          </Button>
          <Button
            variant="secondary"
            onClick={() => router.back()}
            disabled={uploading}
          >
            취소
          </Button>
        </div>
      </Card>
    </div>
  )
}


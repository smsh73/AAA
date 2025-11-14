'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '@/lib/api'
import Table from '@/components/UI/Table'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

interface AnalystFormProps {
  analyst?: Analyst | null
  onSuccess: () => void
  onCancel: () => void
}

function AnalystForm({ analyst, onSuccess, onCancel }: AnalystFormProps) {
  const [formData, setFormData] = useState({
    name: analyst?.name || '',
    firm: analyst?.firm || '',
    department: analyst?.department || '',
    sector: analyst?.sector || '',
    experience_years: analyst?.experience_years || '',
    email: analyst?.email || '',
    profile_url: analyst?.profile_url || '',
    bio: analyst?.bio || '',
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      if (analyst) {
        // 수정
        await api.put(`/api/analysts/${analyst.id}`, formData)
        alert('수정되었습니다.')
      } else {
        // 생성
        await api.post('/api/analysts', formData)
        alert('추가되었습니다.')
      }
      onSuccess()
    } catch (err: any) {
      console.error(err)
      alert(`실패: ${err.response?.data?.detail || err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            이름 <span style={{ color: 'red' }}>*</span>
          </label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            증권사 <span style={{ color: 'red' }}>*</span>
          </label>
          <input
            type="text"
            required
            value={formData.firm}
            onChange={(e) => setFormData({ ...formData, firm: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            부서
          </label>
          <input
            type="text"
            value={formData.department}
            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            섹터
          </label>
          <input
            type="text"
            value={formData.sector}
            onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            경력(년)
          </label>
          <input
            type="number"
            value={formData.experience_years}
            onChange={(e) => setFormData({ ...formData, experience_years: e.target.value ? parseInt(e.target.value) : '' })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            이메일
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
            }}
          />
        </div>
      </div>
      <div>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          프로필 URL
        </label>
        <input
          type="url"
          value={formData.profile_url}
          onChange={(e) => setFormData({ ...formData, profile_url: e.target.value })}
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid var(--fnguide-gray-300)',
            borderRadius: '4px',
          }}
        />
      </div>
      <div>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          소개
        </label>
        <textarea
          value={formData.bio}
          onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
          rows={4}
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid var(--fnguide-gray-300)',
            borderRadius: '4px',
            resize: 'vertical',
          }}
        />
      </div>
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
          취소
        </Button>
        <Button type="submit" variant="primary" disabled={submitting}>
          {submitting ? '처리 중...' : (analyst ? '수정' : '추가')}
        </Button>
      </div>
    </form>
  )
}

interface Analyst {
  id: string
  name: string
  firm: string
  sector?: string
  email?: string
  department?: string
  experience_years?: number
  profile_url?: string
  bio?: string
}

export default function AnalystsPage() {
  const [analysts, setAnalysts] = useState<Analyst[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingAnalyst, setEditingAnalyst] = useState<Analyst | null>(null)

  useEffect(() => {
    loadAnalysts()
  }, [])

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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await api.post('/api/analysts/bulk-import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadResult(res.data)
      alert(`일괄 등록 완료!\n성공: ${res.data.success_count}건\n실패: ${res.data.failed_count}건`)
      
      // 목록 새로고침
      await loadAnalysts()
      setShowUploadForm(false)
    } catch (err: any) {
      console.error(err)
      alert(`일괄 등록 실패: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (analystId: string, analystName: string) => {
    if (!confirm(`정말로 "${analystName}" 애널리스트를 삭제하시겠습니까?`)) {
      return
    }

    try {
      await api.delete(`/api/analysts/${analystId}`)
      alert('삭제되었습니다.')
      await loadAnalysts()
    } catch (err: any) {
      console.error(err)
      alert(`삭제 실패: ${err.response?.data?.detail || err.message}`)
    }
  }

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
        <div style={{ display: 'flex', gap: '8px' }}>
          <Link href={`/analysts/${analyst.id}`}>
            <Button variant="secondary" size="sm">상세</Button>
          </Link>
          <Button 
            variant="secondary" 
            size="sm"
            onClick={() => setEditingAnalyst(analyst)}
          >
            수정
          </Button>
          <Button 
            variant="secondary" 
            size="sm"
            onClick={() => handleDelete(analyst.id, analyst.name)}
            style={{ color: 'var(--fnguide-error)' }}
          >
            삭제
          </Button>
        </div>
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
      <div className="fnguide-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="fnguide-page-title">애널리스트 관리</h1>
          <p className="fnguide-page-subtitle">애널리스트 목록 및 관리</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            추가
          </Button>
          <Button
            variant="secondary"
            onClick={() => setShowUploadForm(!showUploadForm)}
          >
            {showUploadForm ? '닫기' : '일괄 등록'}
          </Button>
        </div>
      </div>

      {(showCreateModal || editingAnalyst) && (
        <div style={{ marginBottom: '24px' }}>
          <Card>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>
              {editingAnalyst ? '애널리스트 수정' : '애널리스트 추가'}
            </h2>
            <AnalystForm
              analyst={editingAnalyst}
              onSuccess={async () => {
                setShowCreateModal(false)
                setEditingAnalyst(null)
                await loadAnalysts()
              }}
              onCancel={() => {
                setShowCreateModal(false)
                setEditingAnalyst(null)
              }}
            />
          </Card>
        </div>
      )}

      {showUploadForm && (
        <div style={{ marginBottom: '24px' }}>
          <Card>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>Excel 파일 일괄 등록</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                Excel 파일 선택
              </label>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid var(--fnguide-gray-300)',
                  borderRadius: '4px',
                }}
              />
            </div>
            {uploading && (
              <div style={{ color: 'var(--fnguide-secondary)', textAlign: 'center', padding: '16px' }}>
                업로드 중...
              </div>
            )}
            {uploadResult && (
              <div style={{ 
                padding: '16px', 
                backgroundColor: 'var(--fnguide-gray-50)', 
                borderRadius: '8px',
                fontSize: '14px'
              }}>
                <div><strong>총 레코드:</strong> {uploadResult.total_records}건</div>
                <div><strong>성공:</strong> {uploadResult.success_count}건</div>
                <div><strong>실패:</strong> {uploadResult.failed_count}건</div>
                {uploadResult.data_collection_started && (
                  <div style={{ marginTop: '8px', color: 'var(--fnguide-primary)' }}>
                    데이터 수집이 자동으로 시작되었습니다.
                  </div>
                )}
              </div>
            )}
          </div>
          </Card>
        </div>
      )}

      <Card>
        {analysts.length > 0 ? (
          <>
            <div style={{ marginBottom: '16px', color: 'var(--fnguide-gray-500)' }}>
              전체 {analysts.length}명
            </div>
            <Table
              columns={columns}
              data={analysts}
              keyExtractor={(item) => item.id}
            />
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
            등록된 애널리스트가 없습니다.
            <br />
            위의 "일괄 등록" 버튼을 클릭하여 Excel 파일을 업로드하세요.
          </div>
        )}
      </Card>
    </div>
  )
}


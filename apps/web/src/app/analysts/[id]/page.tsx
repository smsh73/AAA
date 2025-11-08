'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import Button from '@/components/UI/Button'

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
  const router = useRouter()
  const analystId = params.id as string
  
  const [analyst, setAnalyst] = useState<AnalystDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState<AnalystDetail | null>(null)

  useEffect(() => {
    if (analystId) {
      loadAnalyst()
    }
  }, [analystId])

  const loadAnalyst = async () => {
    try {
      const res = await api.get(`/api/analysts/${analystId}`)
      setAnalyst(res.data)
      setFormData(res.data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!formData) return

    try {
      await api.put(`/api/analysts/${analystId}`, formData)
      alert('수정되었습니다.')
      setEditing(false)
      await loadAnalyst()
    } catch (err: any) {
      console.error(err)
      alert(`수정 실패: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`정말로 "${analyst?.name}" 애널리스트를 삭제하시겠습니까?`)) {
      return
    }

    try {
      await api.delete(`/api/analysts/${analystId}`)
      alert('삭제되었습니다.')
      router.push('/analysts')
    } catch (err: any) {
      console.error(err)
      alert(`삭제 실패: ${err.response?.data?.detail || err.message}`)
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
      <div className="fnguide-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="fnguide-page-title">{analyst.name}</h1>
          <p className="fnguide-page-subtitle">{analyst.firm}</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {!editing ? (
            <>
              <Button variant="secondary" onClick={() => setEditing(true)}>
                수정
              </Button>
              <Button variant="secondary" onClick={handleDelete} style={{ color: 'var(--fnguide-error)' }}>
                삭제
              </Button>
            </>
          ) : (
            <>
              <Button variant="secondary" onClick={() => { setEditing(false); setFormData(analyst) }}>
                취소
              </Button>
              <Button variant="primary" onClick={handleUpdate}>
                저장
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="fnguide-grid fnguide-grid-2">
        <Card title="기본 정보">
          {editing && formData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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
                  value={formData.department || ''}
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
                  value={formData.sector || ''}
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
                  value={formData.experience_years || ''}
                  onChange={(e) => setFormData({ ...formData, experience_years: e.target.value ? parseInt(e.target.value) : undefined })}
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
                  value={formData.email || ''}
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
          ) : (
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
          )}
        </Card>

        <Card title="소개">
          {editing && formData ? (
            <textarea
              value={formData.bio || ''}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              rows={8}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px',
                resize: 'vertical',
              }}
            />
          ) : (
            <p style={{ color: 'var(--fnguide-gray-600)', lineHeight: '1.6' }}>
              {analyst.bio || '소개가 없습니다.'}
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}


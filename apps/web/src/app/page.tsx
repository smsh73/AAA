'use client'

import Link from 'next/link'
import Card from '@/components/UI/Card'

export default function Home() {
  const menuItems = [
    { href: '/dashboard', title: '대시보드', description: '전체 통계 및 현황' },
    { href: '/analysts', title: '애널리스트 관리', description: '애널리스트 등록 및 조회' },
    { href: '/reports', title: '리포트 관리', description: '리포트 업로드 및 추출' },
    { href: '/evaluations', title: '평가 관리', description: '평가 실행 및 결과 조회' },
    { href: '/scorecards', title: '스코어카드', description: '스코어카드 조회 및 랭킹' },
    { href: '/awards', title: '어워즈', description: '어워즈 선정 및 조회' },
    { href: '/data-collection', title: '데이터 수집', description: '데이터 수집 관리' },
    { href: '/logs', title: '로그 관리자', description: 'API 로그 조회 및 다운로드' },
  ]

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">AI가 찾은 스타 애널리스트 어워즈</h1>
        <p className="fnguide-page-subtitle">AI 기반 애널리스트 평가 및 어워즈 시스템</p>
      </div>
      
      <div className="fnguide-grid fnguide-grid-3">
        {menuItems.map((item) => (
          <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
            <Card title={item.title} hover>
              <p style={{ color: 'var(--fnguide-gray-400)', margin: 0 }}>
                {item.description}
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}


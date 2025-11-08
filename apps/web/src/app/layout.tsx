import type { Metadata } from 'next'
import './globals.css'
import '../styles/fnguide.css'
import Layout from '@/components/Layout/Layout'

export const metadata: Metadata = {
  title: 'AI가 찾은 스타 애널리스트 어워즈',
  description: 'AI 기반 애널리스트 평가 및 어워즈 시스템',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>
        <Layout>{children}</Layout>
      </body>
    </html>
  )
}


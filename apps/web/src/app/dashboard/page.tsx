'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Card from '@/components/UI/Card'
import BarChartComponent from '@/components/Charts/BarChart'

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalReports: 0,
    totalEvaluations: 0,
    totalAwards: 0,
    totalAnalysts: 0,
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const res = await api.get('/api/dashboard/stats')
      setStats({
        totalReports: res.data.total_reports || 0,
        totalEvaluations: res.data.total_evaluations || 0,
        totalAwards: res.data.total_awards || 0,
        totalAnalysts: res.data.total_analysts || 0,
      })
    } catch (err) {
      console.error(err)
    }
  }

  const statCards = [
    { title: '전체 리포트', value: stats.totalReports, unit: '건' },
    { title: '평가 완료', value: stats.totalEvaluations, unit: '건' },
    { title: '수상자', value: stats.totalAwards, unit: '명' },
    { title: '등록 애널리스트', value: stats.totalAnalysts, unit: '명' },
  ]

  return (
    <div className="fnguide-container">
      <div className="fnguide-page-header">
        <h1 className="fnguide-page-title">대시보드</h1>
        <p className="fnguide-page-subtitle">시스템 전체 현황 및 통계</p>
      </div>

      <div className="fnguide-grid fnguide-grid-4" style={{ marginBottom: '32px' }}>
        {statCards.map((stat) => (
          <Card key={stat.title} hover>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--fnguide-primary)', marginBottom: '8px' }}>
                {stat.value.toLocaleString()}
              </div>
              <div style={{ fontSize: '14px', color: 'var(--fnguide-gray-500)' }}>
                {stat.title} ({stat.unit})
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="fnguide-grid fnguide-grid-2">
        <Card title="최근 평가 결과">
          <RecentEvaluationsChart />
        </Card>

        <Card title="어워즈 현황">
          <AwardStatusChart />
        </Card>
      </div>
    </div>
  )
}

function RecentEvaluationsChart() {
  const [data, setData] = useState<Array<{ name: string; score: number }>>([])

  useEffect(() => {
    api.get('/api/dashboard/recent-evaluations', { params: { limit: 10 } })
      .then((res) => {
        const evaluations = res.data.evaluations || []
        const chartData = evaluations.map((evaluation: any, index: number) => ({
          name: `평가 ${index + 1}`,
          score: evaluation.final_score || 0,
        }))
        setData(chartData)
      })
      .catch((err) => {
        console.error(err)
      })
  }, [])

  if (data.length === 0) {
    return <div style={{ padding: '24px', textAlign: 'center', color: 'var(--fnguide-gray-400)' }}>데이터가 없습니다.</div>
  }

  return (
    <BarChartComponent
      data={data}
      dataKey="score"
      name="점수"
      color="var(--fnguide-primary)"
    />
  )
}

function AwardStatusChart() {
  const [data, setData] = useState<Array<{ name: string; value: number }>>([])

  useEffect(() => {
    api.get('/api/dashboard/award-status')
      .then((res) => {
        const awards = res.data.awards_by_category || []
        const chartData = awards.map((award: any) => ({
          name: award.category,
          value: award.total,
        }))
        setData(chartData)
      })
      .catch((err) => {
        console.error(err)
      })
  }, [])

  if (data.length === 0) {
    return <div style={{ padding: '24px', textAlign: 'center', color: 'var(--fnguide-gray-400)' }}>데이터가 없습니다.</div>
  }

  return (
    <BarChartComponent
      data={data}
      dataKey="value"
      name="수상자 수"
      color="var(--fnguide-secondary)"
    />
  )
}

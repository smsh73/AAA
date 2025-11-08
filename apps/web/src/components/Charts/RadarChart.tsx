'use client'

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend } from 'recharts'

interface RadarChartProps {
  data: Array<{ name: string; value: number }>
  name: string
  color?: string
}

export default function RadarChartComponent({ data, name, color = '#0066CC' }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="name" />
        <PolarRadiusAxis angle={90} domain={[0, 100]} />
        <Radar name={name} dataKey="value" stroke={color} fill={color} fillOpacity={0.6} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  )
}


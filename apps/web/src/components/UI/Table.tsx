'use client'

import { ReactNode, useState, useMemo } from 'react'
import Button from './Button'

interface TableColumn<T> {
  key: string
  label: string
  render?: (item: T) => ReactNode
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
}

interface TableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  keyExtractor: (item: T) => string
  sortable?: boolean
  filterable?: boolean
  exportable?: boolean
  onExport?: () => void
  pagination?: {
    page: number
    limit: number
    total: number
    onPageChange: (page: number) => void
    onLimitChange: (limit: number) => void
  }
}

type SortDirection = 'asc' | 'desc' | null

export default function Table<T>({
  columns,
  data,
  keyExtractor,
  sortable = true,
  filterable = false,
  exportable = false,
  onExport,
  pagination
}: TableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const [filterText, setFilterText] = useState('')

  const handleSort = (columnKey: string) => {
    if (!sortable) return
    
    if (sortColumn === columnKey) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data

    return [...data].sort((a, b) => {
      const aValue = (a as any)[sortColumn]
      const bValue = (b as any)[sortColumn]

      if (aValue === null || aValue === undefined) return 1
      if (bValue === null || bValue === undefined) return -1

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      const aStr = String(aValue).toLowerCase()
      const bStr = String(bValue).toLowerCase()

      if (sortDirection === 'asc') {
        return aStr.localeCompare(bStr)
      } else {
        return bStr.localeCompare(aStr)
      }
    })
  }, [data, sortColumn, sortDirection])

  const filteredData = useMemo(() => {
    if (!filterText) return sortedData

    return sortedData.filter((item) => {
      return columns.some((column) => {
        const value = (item as any)[column.key]
        return String(value || '').toLowerCase().includes(filterText.toLowerCase())
      })
    })
  }, [sortedData, filterText, columns])

  const exportToCSV = () => {
    const headers = columns.map(col => col.label).join(',')
    const rows = filteredData.map(item =>
      columns.map(col => {
        const value = col.render ? String(col.render(item)) : (item as any)[col.key]
        return `"${String(value || '').replace(/"/g, '""')}"`
      }).join(',')
    )
    const csv = [headers, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  const displayData = pagination
    ? filteredData.slice(
        (pagination.page - 1) * pagination.limit,
        pagination.page * pagination.limit
      )
    : filteredData

  return (
    <div>
      {(filterable || exportable) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', gap: '16px' }}>
          {filterable && (
            <input
              type="text"
              placeholder="검색..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid var(--fnguide-gray-300)',
                borderRadius: '4px'
              }}
            />
          )}
          {exportable && (
            <Button variant="secondary" onClick={onExport || exportToCSV}>
              CSV 내보내기
            </Button>
          )}
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table className="fnguide-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() => column.sortable !== false && sortable && handleSort(column.key)}
                  style={{
                    cursor: column.sortable !== false && sortable ? 'pointer' : 'default',
                    textAlign: column.align || 'left',
                    userSelect: 'none',
                    padding: '12px',
                    borderBottom: '2px solid var(--fnguide-gray-300)',
                    backgroundColor: 'var(--fnguide-gray-50)',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {column.label}
                    {sortable && column.sortable !== false && sortColumn === column.key && (
                      <span style={{ fontSize: '12px' }}>
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.length > 0 ? (
              displayData.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  style={{
                    borderBottom: '1px solid var(--fnguide-gray-200)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--fnguide-gray-50)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'white'
                  }}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      style={{
                        padding: '12px',
                        textAlign: column.align || 'left'
                      }}
                    >
                      {column.render
                        ? column.render(item)
                        : (item as any)[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '48px', color: 'var(--fnguide-gray-400)' }}>
                  데이터가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {pagination && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
          <div style={{ color: 'var(--fnguide-gray-500)' }}>
            총 {pagination.total}개 중 {((pagination.page - 1) * pagination.limit) + 1}-
            {Math.min(pagination.page * pagination.limit, pagination.total)}개 표시
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
            >
              이전
            </Button>
            <span style={{ minWidth: '100px', textAlign: 'center' }}>
              {pagination.page} / {Math.ceil(pagination.total / pagination.limit)}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.page + 1)}
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.limit)}
            >
              다음
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

'use client'

import { ReactNode } from 'react'

interface TableColumn<T> {
  key: string
  label: string
  render?: (item: T) => ReactNode
}

interface TableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  keyExtractor: (item: T) => string
}

export default function Table<T>({ columns, data, keyExtractor }: TableProps<T>) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="fnguide-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={keyExtractor(item)}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(item)
                    : (item as any)[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


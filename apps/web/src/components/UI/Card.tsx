'use client'

import { ReactNode } from 'react'
import clsx from 'clsx'

interface CardProps {
  title?: string
  children: ReactNode
  className?: string
  hover?: boolean
}

export default function Card({ title, children, className, hover = true }: CardProps) {
  return (
    <div className={clsx('fnguide-card', hover && 'hover:shadow-md', className)}>
      {title && (
        <div className="fnguide-card-header">
          <h3 className="fnguide-card-title">{title}</h3>
        </div>
      )}
      <div>{children}</div>
    </div>
  )
}


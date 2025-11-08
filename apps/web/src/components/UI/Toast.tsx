'use client'

import { useEffect, useState } from 'react'
import clsx from 'clsx'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastProps {
  message: string
  type?: ToastType
  duration?: number
  onClose: () => void
}

export default function Toast({ message, type = 'info', duration = 3000, onClose }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  const typeStyles = {
    success: {
      backgroundColor: 'var(--fnguide-success)',
      color: 'white'
    },
    error: {
      backgroundColor: 'var(--fnguide-error)',
      color: 'white'
    },
    warning: {
      backgroundColor: 'var(--fnguide-warning)',
      color: 'white'
    },
    info: {
      backgroundColor: 'var(--fnguide-primary)',
      color: 'white'
    }
  }

  return (
    <div
      className="fnguide-toast"
      style={{
        position: 'fixed',
        top: '24px',
        right: '24px',
        padding: '16px 24px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        zIndex: 2000,
        minWidth: '300px',
        maxWidth: '500px',
        ...typeStyles[type]
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{message}</span>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontSize: '20px',
            marginLeft: '16px',
            padding: 0,
            width: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          aria-label="닫기"
        >
          ×
        </button>
      </div>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Array<{ id: string; message: string; type: ToastType }>
  onRemove: (id: string) => void
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div style={{ position: 'fixed', top: '24px', right: '24px', zIndex: 2000 }}>
      {toasts.map((toast, index) => (
        <div key={toast.id} style={{ marginBottom: index < toasts.length - 1 ? '8px' : 0 }}>
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => onRemove(toast.id)}
          />
        </div>
      ))}
    </div>
  )
}


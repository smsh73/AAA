'use client'

import { ReactNode } from 'react'

interface StepperProps {
  steps: Array<{ label: string; description?: string }>
  currentStep: number
  completedSteps?: number[]
}

export default function Stepper({ steps, currentStep, completedSteps = [] }: StepperProps) {
  return (
    <div className="fnguide-stepper" style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
      {steps.map((step, index) => {
        const isCompleted = completedSteps.includes(index) || index < currentStep
        const isCurrent = index === currentStep
        const isPast = index < currentStep

        return (
          <div key={index} style={{ display: 'flex', alignItems: 'flex-start', flex: 1 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: isCompleted
                    ? 'var(--fnguide-primary)'
                    : isCurrent
                    ? 'var(--fnguide-gray-200)'
                    : 'var(--fnguide-gray-100)',
                  color: isCompleted ? 'white' : 'var(--fnguide-gray-600)',
                  fontWeight: 600,
                  border: isCurrent ? '2px solid var(--fnguide-primary)' : 'none',
                  marginBottom: '8px'
                }}
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              <div style={{ textAlign: 'center', maxWidth: '150px' }}>
                <div
                  style={{
                    fontWeight: isCurrent ? 600 : 400,
                    fontSize: '14px',
                    color: isCurrent || isPast ? 'var(--fnguide-gray-900)' : 'var(--fnguide-gray-500)'
                  }}
                >
                  {step.label}
                </div>
                {step.description && (
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--fnguide-gray-500)',
                      marginTop: '4px'
                    }}
                  >
                    {step.description}
                  </div>
                )}
              </div>
            </div>
            {index < steps.length - 1 && (
              <div
                style={{
                  width: '100%',
                  height: '2px',
                  backgroundColor: isCompleted ? 'var(--fnguide-primary)' : 'var(--fnguide-gray-200)',
                  marginTop: '16px',
                  marginLeft: '16px',
                  marginRight: '16px'
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}


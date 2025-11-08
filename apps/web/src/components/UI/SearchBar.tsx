'use client'

import { useState, useEffect, useRef } from 'react'
import Button from './Button'

interface SearchBarProps {
  placeholder?: string
  onSearch: (query: string) => void
  suggestions?: string[]
  filters?: Array<{ key: string; label: string; options: string[] }>
  onFilterChange?: (filters: Record<string, string>) => void
}

export default function SearchBar({
  placeholder = '검색...',
  onSearch,
  suggestions = [],
  filters = [],
  onFilterChange
}: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({})
  const [showFilters, setShowFilters] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
        setShowFilters(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSearch = () => {
    onSearch(query)
    setShowSuggestions(false)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...activeFilters, [key]: value }
    setActiveFilters(newFilters)
    if (onFilterChange) {
      onFilterChange(newFilters)
    }
  }

  return (
    <div ref={searchRef} style={{ position: 'relative', width: '100%' }}>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowSuggestions(suggestions.length > 0)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid var(--fnguide-gray-300)',
              borderRadius: '4px',
              fontSize: '16px'
            }}
          />
          {showSuggestions && suggestions.length > 0 && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                backgroundColor: 'white',
                border: '1px solid var(--fnguide-gray-200)',
                borderRadius: '4px',
                marginTop: '4px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                zIndex: 100,
                maxHeight: '200px',
                overflowY: 'auto'
              }}
            >
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => {
                    setQuery(suggestion)
                    onSearch(suggestion)
                    setShowSuggestions(false)
                  }}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: index < suggestions.length - 1 ? '1px solid var(--fnguide-gray-100)' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--fnguide-gray-50)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'white'
                  }}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          )}
        </div>
        <Button onClick={handleSearch}>검색</Button>
        {filters.length > 0 && (
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
          >
            필터
          </Button>
        )}
      </div>
      {showFilters && filters.length > 0 && (
        <div
          style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: 'var(--fnguide-gray-50)',
            borderRadius: '8px',
            border: '1px solid var(--fnguide-gray-200)'
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filters.map((filter) => (
              <div key={filter.key}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  {filter.label}
                </label>
                <select
                  value={activeFilters[filter.key] || ''}
                  onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid var(--fnguide-gray-300)',
                    borderRadius: '4px'
                  }}
                >
                  <option value="">전체</option>
                  {filter.options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


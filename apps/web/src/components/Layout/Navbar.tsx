'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import '../../styles/fnguide.css'

export default function Navbar() {
  const pathname = usePathname()

  const menuItems = [
    { href: '/dashboard', label: '대시보드' },
    { href: '/analysts', label: '애널리스트' },
    { href: '/companies', label: '기업' },
    { href: '/reports', label: '리포트' },
    { href: '/evaluations', label: '평가' },
    { href: '/scorecards', label: '스코어카드' },
    { href: '/awards', label: '어워즈' },
    { href: '/data-collection', label: '데이터 수집' },
    { href: '/agents', label: '에이전트' },
  ]

  return (
    <nav className="fnguide-navbar">
      <div className="fnguide-navbar-content">
        <Link href="/" className="fnguide-navbar-brand">
          AI가 찾은 스타 애널리스트
        </Link>
        <ul className="fnguide-navbar-menu">
          {menuItems.map((item) => (
            <li key={item.href} className="fnguide-navbar-item">
              <Link
                href={item.href}
                className={`fnguide-navbar-link ${
                  pathname?.startsWith(item.href) ? 'active' : ''
                }`}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}


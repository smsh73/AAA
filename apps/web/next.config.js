/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Next.js에서 환경변수는 NEXT_PUBLIC_ 접두사가 있어야 클라이언트에서 접근 가능
  // env는 서버 사이드에서만 사용 가능하므로 제거
  // 클라이언트에서는 process.env.NEXT_PUBLIC_API_URL 사용
  
  // 개발 환경에서 /api/* 요청을 백엔드로 프록시
  async rewrites() {
    const backendUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // NEXT_PUBLIC_API_URL이 빈 문자열이거나 설정되지 않은 경우에만 프록시 사용
    if (!process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_URL.trim() === '') {
      return [
        {
          source: '/api/:path*',
          destination: `${backendUrl}/api/:path*`,
        },
      ]
    }
    
    return []
  },
}

module.exports = nextConfig


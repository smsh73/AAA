/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Next.js에서 환경변수는 NEXT_PUBLIC_ 접두사가 있어야 클라이언트에서 접근 가능
  // env는 서버 사이드에서만 사용 가능하므로 제거
  // 클라이언트에서는 process.env.NEXT_PUBLIC_API_URL 사용
}

module.exports = nextConfig


import axios from 'axios'

// 환경변수에서 API URL 가져오기
// 개발 환경: NEXT_PUBLIC_API_URL 또는 API_URL 환경변수 사용
// 프로덕션: NEXT_PUBLIC_API_URL 필수
// 빈 문자열이거나 설정되지 않으면 상대 경로 사용 (Next.js rewrites 활용)
const getApiUrl = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  
  // 빈 문자열이거나 설정되지 않은 경우 상대 경로 사용
  // Next.js rewrites를 통해 /api/* 요청을 백엔드로 프록시
  if (!apiUrl || apiUrl.trim() === '') {
    return ''
  }
  
  return apiUrl
}

const API_URL = getApiUrl()

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 요청 인터셉터: 에러 처리
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터: 에러 처리
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // 서버에서 응답이 왔지만 에러 상태 코드
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // 요청은 보냈지만 응답을 받지 못함
      console.error('API Request Error: No response received', error.request)
    } else {
      // 요청 설정 중 에러
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api


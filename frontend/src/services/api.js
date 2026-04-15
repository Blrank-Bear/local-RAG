import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

// Attach JWT token to every request
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear token so the app redirects to login
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.dispatchEvent(new Event('auth:logout'))
    }
    return Promise.reject(err)
  },
)

export const api = {
  // Auth
  register: (username, email, password) =>
    http.post('/auth/register', { username, email, password }).then((r) => r.data),

  login: (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return http
      .post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
      .then((r) => r.data)
  },

  me: () => http.get('/auth/me').then((r) => r.data),

  // Chat — simple POST, returns full response
  chat: (query, sessionId) =>
    http.post('/chat/', { query, session_id: sessionId }).then((r) => r.data),

  // History
  getHistory: (sessionId) =>
    http.get(`/chat/history/${sessionId}`).then((r) => r.data),

  deleteHistory: (sessionId) =>
    http.delete(`/chat/history/${sessionId}`),

  // Sessions
  getSessions: () =>
    http.get('/chat/sessions').then((r) => r.data),

  deleteSession: (sessionId) =>
    http.delete(`/chat/sessions/${sessionId}`),

  // Voice — POST audio blob, returns { transcript }
  transcribe: (audioBlob) => {
    const form = new FormData()
    form.append('file', audioBlob, 'audio.webm')
    return http.post('/voice/transcribe', form).then((r) => r.data)
  },

  // Documents
  listDocuments: () => http.get('/documents/').then((r) => r.data),
  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/documents/upload', form).then((r) => r.data)
  },

  // Tasks
  runTask: (query, sessionId) =>
    http.post('/tasks/run', { query, session_id: sessionId }).then((r) => r.data),

  // Feedback
  submitFeedback: (sessionId, messageId, rating, comment) =>
    http.post('/feedback/', { session_id: sessionId, message_id: messageId, rating, comment })
      .then((r) => r.data),

  getRatedMessages: (sessionId) =>
    http.get(`/feedback/rated/${sessionId}`).then((r) => r.data),

  getStats: (sessionId) =>
    http.get(`/feedback/stats/${sessionId}`).then((r) => r.data),

  health: () => http.get('/health').then((r) => r.data),
}

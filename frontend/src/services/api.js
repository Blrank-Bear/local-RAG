import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export const api = {
  // Chat — simple POST, returns full response
  chat: (query, sessionId) =>
    http.post('/chat/', { query, session_id: sessionId }).then((r) => r.data),

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

  getStats: (sessionId) =>
    http.get(`/feedback/stats/${sessionId}`).then((r) => r.data),

  health: () => http.get('/health').then((r) => r.data),
}

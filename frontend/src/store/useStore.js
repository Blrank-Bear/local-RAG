import { create } from 'zustand'

// Rehydrate auth from localStorage on page load
const storedUser = (() => {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
})()
const storedToken = localStorage.getItem('token') || null

export const useStore = create((set, get) => ({
  // ── Auth ──────────────────────────────────────────────────────────────────
  token: storedToken,
  user: storedUser,   // { user_id, username }
  isAuthenticated: !!storedToken,

  setAuth: (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      messages: [],
      sessionId: null,
      agentStatus: null,
    })
  },

  // ── Session ───────────────────────────────────────────────────────────────
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),

  // ── Messages ──────────────────────────────────────────────────────────────
  messages: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),

  // ── Agent status ──────────────────────────────────────────────────────────
  agentStatus: null,   // { status, agent }
  setAgentStatus: (status) => set({ agentStatus: status }),

  // ── Active panel ──────────────────────────────────────────────────────────
  activePanel: 'chat',  // 'chat' | 'documents' | 'tasks' | 'feedback'
  setActivePanel: (panel) => set({ activePanel: panel }),

  // ── Voice ─────────────────────────────────────────────────────────────────
  isRecording: false,
  setIsRecording: (v) => set({ isRecording: v }),
  voiceMode: 'push_to_talk',  // 'push_to_talk' | 'continuous'
  setVoiceMode: (m) => set({ voiceMode: m }),

  // ── Documents ─────────────────────────────────────────────────────────────
  documents: [],
  setDocuments: (docs) => set({ documents: docs }),

  // ── Loading ───────────────────────────────────────────────────────────────
  isLoading: false,
  setIsLoading: (v) => set({ isLoading: v }),
}))

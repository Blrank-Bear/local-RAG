import { create } from 'zustand'

// Rehydrate auth + session from localStorage on page load
const storedUser = (() => {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
})()
const storedToken = localStorage.getItem('token') || null
const storedSessionId = localStorage.getItem('sessionId') || null

export const useStore = create((set, get) => ({
  // ── Auth ──────────────────────────────────────────────────────────────────
  token: storedToken,
  user: storedUser,
  isAuthenticated: !!storedToken,

  setAuth: (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('sessionId')
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      messages: [],
      ratedMessages: {},
      sessionId: null,
      agentStatus: null,
      sessions: [],
    })
  },

  // ── Session ───────────────────────────────────────────────────────────────
  sessionId: storedSessionId,
  setSessionId: (id) => {
    if (id) localStorage.setItem('sessionId', id)
    else localStorage.removeItem('sessionId')
    set({ sessionId: id })
  },

  // ── Session list (sidebar) ────────────────────────────────────────────────
  sessions: [],
  setSessions: (sessions) => set({ sessions }),

  // ── Messages ──────────────────────────────────────────────────────────────
  messages: [],
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),

  // ── Rated messages { messageId: rating } ─────────────────────────────────
  ratedMessages: {},   // persisted in store; loaded from DB on session restore
  setRatedMessages: (map) => set({ ratedMessages: map }),
  markRated: (messageId, rating) =>
    set((s) => ({ ratedMessages: { ...s.ratedMessages, [messageId]: rating } })),

  // ── Agent status ──────────────────────────────────────────────────────────
  agentStatus: null,
  setAgentStatus: (status) => set({ agentStatus: status }),

  // ── Active panel ──────────────────────────────────────────────────────────
  activePanel: 'chat',
  setActivePanel: (panel) => set({ activePanel: panel }),

  // ── Voice ─────────────────────────────────────────────────────────────────
  isRecording: false,
  setIsRecording: (v) => set({ isRecording: v }),
  voiceMode: 'push_to_talk',
  setVoiceMode: (m) => set({ voiceMode: m }),

  // ── Documents ─────────────────────────────────────────────────────────────
  documents: [],
  setDocuments: (docs) => set({ documents: docs }),

  // ── Loading ───────────────────────────────────────────────────────────────
  isLoading: false,
  setIsLoading: (v) => set({ isLoading: v }),
}))

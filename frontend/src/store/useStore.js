import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Session
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),

  // Messages
  messages: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),

  // Agent status
  agentStatus: null,   // { status, agent }
  setAgentStatus: (status) => set({ agentStatus: status }),

  // Active panel
  activePanel: 'chat',  // 'chat' | 'documents' | 'tasks' | 'feedback'
  setActivePanel: (panel) => set({ activePanel: panel }),

  // Voice
  isRecording: false,
  setIsRecording: (v) => set({ isRecording: v }),
  voiceMode: 'push_to_talk',  // 'push_to_talk' | 'continuous'
  setVoiceMode: (m) => set({ voiceMode: m }),

  // Documents
  documents: [],
  setDocuments: (docs) => set({ documents: docs }),

  // Loading
  isLoading: false,
  setIsLoading: (v) => set({ isLoading: v }),
}))

import React, { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import './Sidebar.css'

const NAV = [
  { id: 'chat',      icon: '💬', label: 'Chat' },
  { id: 'documents', icon: '📄', label: 'Documents' },
  { id: 'tasks',     icon: '⚡', label: 'Tasks' },
  { id: 'feedback',  icon: '📊', label: 'Feedback' },
]

export default function Sidebar() {
  const {
    activePanel, setActivePanel,
    setMessages, setSessionId, sessionId,
    sessions, setSessions,
    setRatedMessages,
    user, logout,
  } = useStore()

  const [deletingId, setDeletingId] = useState(null)

  // Load session list on mount and whenever we switch to chat
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await api.getSessions()
      setSessions(data)
    } catch {
      // not authenticated yet or network error — ignore
    }
  }

  const newSession = () => {
    const id = crypto.randomUUID()
    setSessionId(id)
    setMessages([])
    setRatedMessages({})
    setActivePanel('chat')
  }

  const switchSession = async (id) => {
    if (id === sessionId) {
      setActivePanel('chat')
      return
    }
    setSessionId(id)
    setMessages([])
    setRatedMessages({})
    setActivePanel('chat')
    try {
      const [history, rated] = await Promise.all([
        api.getHistory(id),
        api.getRatedMessages(id),
      ])
      setMessages(history.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        retrieved_context: m.retrieved_context || [],
      })))
      setRatedMessages(rated)
    } catch {
      // session may be empty
    }
  }

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation()
    setDeletingId(id)
    try {
      await api.deleteSession(id)
      // If we deleted the active session, start fresh
      if (id === sessionId) {
        const newId = crypto.randomUUID()
        setSessionId(newId)
        setMessages([])
      }
      await loadSessions()
    } catch (err) {
      console.error('Delete session failed:', err)
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (iso) => {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now - d
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHrs = Math.floor(diffMins / 60)
    if (diffHrs < 24) return `${diffHrs}h ago`
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo">⬡</span>
        <span className="sidebar__title">AgentOS</span>
      </div>

      <nav className="sidebar__nav">
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`sidebar__item ${activePanel === item.id ? 'sidebar__item--active' : ''}`}
            onClick={() => setActivePanel(item.id)}
          >
            <span className="sidebar__icon">{item.icon}</span>
            <span className="sidebar__label">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Session history list */}
      <div className="sidebar__sessions">
        <div className="sidebar__sessions-header">
          <span className="sidebar__sessions-title">Sessions</span>
          <button
            className="sidebar__new-session-icon"
            onClick={newSession}
            title="New session"
            aria-label="New session"
          >
            ＋
          </button>
        </div>

        <div className="sidebar__sessions-list">
          {sessions.length === 0 && (
            <p className="sidebar__sessions-empty">No sessions yet.</p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar__session ${s.id === sessionId ? 'sidebar__session--active' : ''}`}
              onClick={() => switchSession(s.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && switchSession(s.id)}
            >
              <div className="sidebar__session-body">
                <span className="sidebar__session-preview">
                  {s.last_message || 'Empty session'}
                </span>
                <span className="sidebar__session-meta">
                  {formatDate(s.updated_at)} · {s.message_count} msg{s.message_count !== 1 ? 's' : ''}
                </span>
              </div>
              <button
                className="sidebar__session-delete"
                onClick={(e) => handleDeleteSession(e, s.id)}
                disabled={deletingId === s.id}
                title="Delete session"
                aria-label="Delete session"
              >
                {deletingId === s.id ? '…' : '✕'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="sidebar__footer">
        <button className="sidebar__new-session" onClick={newSession}>
          + New Session
        </button>

        {user && (
          <div className="sidebar__user">
            <span className="sidebar__user-avatar">
              {user.username?.[0]?.toUpperCase() ?? '?'}
            </span>
            <span className="sidebar__user-name">{user.username}</span>
            <button
              className="sidebar__logout"
              onClick={logout}
              title="Sign out"
              aria-label="Sign out"
            >
              ⏻
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}

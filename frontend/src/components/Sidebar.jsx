import React from 'react'
import { useStore } from '../store/useStore'
import './Sidebar.css'

const NAV = [
  { id: 'chat',      icon: '💬', label: 'Chat' },
  { id: 'documents', icon: '📄', label: 'Documents' },
  { id: 'tasks',     icon: '⚡', label: 'Tasks' },
  { id: 'feedback',  icon: '📊', label: 'Feedback' },
]

export default function Sidebar() {
  const { activePanel, setActivePanel, clearMessages, setSessionId, user, logout } = useStore()

  const newSession = () => {
    setSessionId(crypto.randomUUID())
    clearMessages()
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

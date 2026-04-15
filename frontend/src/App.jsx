import React, { useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import DocumentsPanel from './components/DocumentsPanel'
import TasksPanel from './components/TasksPanel'
import FeedbackPanel from './components/FeedbackPanel'
import AuthPage from './components/AuthPage'
import { useStore } from './store/useStore'
import './App.css'

const PANELS = {
  chat:      <ChatPanel />,
  documents: <DocumentsPanel />,
  tasks:     <TasksPanel />,
  feedback:  <FeedbackPanel />,
}

export default function App() {
  const activePanel = useStore((s) => s.activePanel)
  const isAuthenticated = useStore((s) => s.isAuthenticated)
  const logout = useStore((s) => s.logout)

  // Handle token expiry / 401 from anywhere in the app
  useEffect(() => {
    const handler = () => logout()
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [logout])

  if (!isAuthenticated) {
    return <AuthPage />
  }

  return (
    <div className="app">
      <Sidebar />
      <main className="app__main">
        {PANELS[activePanel]}
      </main>
    </div>
  )
}

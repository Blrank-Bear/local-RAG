import React from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import DocumentsPanel from './components/DocumentsPanel'
import TasksPanel from './components/TasksPanel'
import FeedbackPanel from './components/FeedbackPanel'
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

  return (
    <div className="app">
      <Sidebar />
      <main className="app__main">
        {PANELS[activePanel]}
      </main>
    </div>
  )
}

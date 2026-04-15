import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import MessageBubble from './MessageBubble'
import VoiceInput from './VoiceInput'
import AgentStatus from './AgentStatus'
import './ChatPanel.css'

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [deletingHistory, setDeletingHistory] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  const {
    messages, setMessages, addMessage,
    sessionId, setSessionId,
    isLoading, setIsLoading,
    agentStatus, setAgentStatus,
    setSessions,
    setRatedMessages,
  } = useStore()

  // ── On mount: restore session and load history from DB ──────────────────
  useEffect(() => {
    const init = async () => {
      let sid = sessionId

      // If no session yet, create one
      if (!sid) {
        sid = crypto.randomUUID()
        setSessionId(sid)
      }

      // Load persisted messages and rated state in parallel
      try {
        const [history, rated] = await Promise.all([
          api.getHistory(sid),
          api.getRatedMessages(sid),
        ])
        if (history.length > 0) {
          setMessages(history.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            retrieved_context: m.retrieved_context || [],
          })))
        }
        setRatedMessages(rated)
      } catch (err) {
        // 404 = session doesn't exist in DB yet (first message will create it)
        if (err?.response?.status !== 404) {
          console.warn('Could not load history:', err.message)
        }
      }
    }
    init()
  }, []) // run once on mount

  // ── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, agentStatus])

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    const query = text.trim()
    if (!query || isLoading) return

    let sid = sessionId
    if (!sid) {
      sid = crypto.randomUUID()
      setSessionId(sid)
    }

    addMessage({ id: crypto.randomUUID(), role: 'user', content: query })
    setIsLoading(true)
    setInput('')
    setAgentStatus({ status: 'Thinking...', agent: 'executor' })

    try {
      const data = await api.chat(query, sid)
      addMessage({
        id: data.message_id || crypto.randomUUID(),
        role: 'assistant',
        content: data.response || '_(no response)_',
        retrieved_context: data.retrieved_context || [],
      })
      // Refresh session list in sidebar
      const sessions = await api.getSessions()
      setSessions(sessions)
    } catch (err) {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `⚠️ Error: ${err?.response?.data?.detail || err.message}`,
        retrieved_context: [],
      })
    } finally {
      setAgentStatus(null)
      setIsLoading(false)
    }
  }, [isLoading, sessionId, addMessage, setIsLoading, setAgentStatus, setSessionId, setSessions])

  // ── Delete history ───────────────────────────────────────────────────────
  const handleDeleteHistory = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    if (!sessionId) return
    setDeletingHistory(true)
    try {
      await api.deleteHistory(sessionId)
      setMessages([])
      setRatedMessages({})
      const sessions = await api.getSessions()
      setSessions(sessions)
    } catch (err) {
      console.error('Delete history failed:', err)
    } finally {
      setDeletingHistory(false)
      setConfirmDelete(false)
    }
  }

  const cancelDelete = () => setConfirmDelete(false)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
    if (e.key === 'Escape' && confirmDelete) {
      cancelDelete()
    }
  }

  const handleTranscript = useCallback((text) => {
    setInput(text)
    sendMessage(text)
  }, [sendMessage])

  return (
    <div className="chat-panel">
      {/* Header with delete button */}
      {messages.length > 0 && (
        <div className="chat-panel__header">
          {confirmDelete ? (
            <div className="chat-panel__confirm">
              <span>Delete all messages in this session?</span>
              <button
                className="chat-panel__confirm-yes"
                onClick={handleDeleteHistory}
                disabled={deletingHistory}
              >
                {deletingHistory ? <span className="chat-panel__spinner" /> : 'Delete'}
              </button>
              <button className="chat-panel__confirm-no" onClick={cancelDelete}>
                Cancel
              </button>
            </div>
          ) : (
            <button
              className="chat-panel__delete-btn"
              onClick={handleDeleteHistory}
              title="Delete conversation history"
              aria-label="Delete conversation history"
            >
              🗑 Clear history
            </button>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <div className="chat-panel__empty">
            <span className="chat-panel__empty-icon">⬡</span>
            <p>Ask anything. I'll retrieve, analyze, and respond.</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {agentStatus && (
          <div className="chat-panel__status-wrap">
            <AgentStatus />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-panel__input-area">
        <VoiceInput onTranscript={handleTranscript} />

        <div className="chat-panel__input-wrap">
          <textarea
            ref={textareaRef}
            className="chat-panel__textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or describe a task..."
            rows={1}
            disabled={isLoading}
          />
          <button
            className="chat-panel__send"
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
          >
            {isLoading ? <span className="chat-panel__spinner" /> : '↑'}
          </button>
        </div>
      </div>
    </div>
  )
}

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import MessageBubble from './MessageBubble'
import VoiceInput from './VoiceInput'
import AgentStatus from './AgentStatus'
import './ChatPanel.css'

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  const {
    messages, addMessage, sessionId, setSessionId,
    isLoading, setIsLoading, agentStatus, setAgentStatus,
  } = useStore()

  // Assign session ID once on mount
  useEffect(() => {
    if (!sessionId) setSessionId(crypto.randomUUID())
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, agentStatus])

  const sendMessage = useCallback(async (text) => {
    const query = text.trim()
    if (!query || isLoading) return

    const sid = sessionId || crypto.randomUUID()
    if (!sessionId) setSessionId(sid)

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
  }, [isLoading, sessionId, addMessage, setIsLoading, setAgentStatus, setSessionId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleTranscript = useCallback((text) => {
    setInput(text)
    sendMessage(text)
  }, [sendMessage])

  return (
    <div className="chat-panel">
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

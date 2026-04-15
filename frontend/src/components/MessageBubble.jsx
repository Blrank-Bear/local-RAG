import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './MessageBubble.css'

export default function MessageBubble({ message }) {
  const [rated, setRated] = useState(false)
  const [showContext, setShowContext] = useState(false)
  const sessionId = useStore((s) => s.sessionId)

  const isUser = message.role === 'user'

  const handleRate = async (rating) => {
    if (rated) return
    await api.submitFeedback(sessionId, message.id, rating, null)
    setRated(true)
  }

  return (
    <div className={`bubble-wrap ${isUser ? 'bubble-wrap--user' : 'bubble-wrap--assistant'}`}>
      <div className="bubble__avatar">
        {isUser ? '👤' : '⬡'}
      </div>

      <div className="bubble__body">
        <div className={`bubble ${isUser ? 'bubble--user' : 'bubble--assistant'}`}>
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {!isUser && (
          <div className="bubble__actions">
            {message.retrieved_context?.length > 0 && (
              <button
                className="bubble__action-btn"
                onClick={() => setShowContext((v) => !v)}
              >
                {showContext ? 'Hide' : 'Show'} sources ({message.retrieved_context.length})
              </button>
            )}

            {!rated ? (
              <div className="bubble__rating">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} className="bubble__star" onClick={() => handleRate(n)}>
                    ★
                  </button>
                ))}
              </div>
            ) : (
              <span className="bubble__rated">Rated ✓</span>
            )}
          </div>
        )}

        {showContext && message.retrieved_context?.length > 0 && (
          <div className="bubble__context">
            {message.retrieved_context.map((ctx, i) => (
              <div key={i} className="bubble__context-item">
                <span className="bubble__context-source">{ctx.source}</span>
                <p className="bubble__context-text">{ctx.content}</p>
                <span className="bubble__context-score">score: {ctx.score}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

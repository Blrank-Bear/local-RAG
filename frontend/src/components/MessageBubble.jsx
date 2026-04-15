import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './MessageBubble.css'

export default function MessageBubble({ message }) {
  const [showContext, setShowContext] = useState(false)
  const [hoveredStar, setHoveredStar] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const sessionId = useStore((s) => s.sessionId)
  const ratedMessages = useStore((s) => s.ratedMessages)
  const markRated = useStore((s) => s.markRated)

  const isUser = message.role === 'user'
  const existingRating = ratedMessages[message.id] ?? null
  const isRated = existingRating !== null

  const handleRate = async (rating) => {
    if (isRated || submitting) return
    setSubmitting(true)
    try {
      await api.submitFeedback(sessionId, message.id, rating, null)
      markRated(message.id, rating)
    } catch (err) {
      // 409 = already rated (race condition or duplicate click) — still mark locally
      if (err?.response?.status === 409) {
        markRated(message.id, rating)
      } else {
        console.error('Rating failed:', err)
      }
    } finally {
      setSubmitting(false)
    }
  }

  // Determine star fill state for display
  const getStarState = (n) => {
    if (isRated) return n <= existingRating ? 'filled' : 'empty'
    if (hoveredStar > 0) return n <= hoveredStar ? 'hovered' : 'empty'
    return 'empty'
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

            <div
              className={`bubble__rating ${isRated ? 'bubble__rating--locked' : ''}`}
              title={isRated ? `You rated this ${existingRating} out of 5` : 'Rate this response'}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  className={`bubble__star bubble__star--${getStarState(n)}`}
                  onClick={() => handleRate(n)}
                  onMouseEnter={() => !isRated && setHoveredStar(n)}
                  onMouseLeave={() => !isRated && setHoveredStar(0)}
                  disabled={isRated || submitting}
                  aria-label={isRated ? `Rated ${existingRating} stars` : `Rate ${n} star${n > 1 ? 's' : ''}`}
                >
                  ★
                </button>
              ))}
              {isRated && (
                <span className="bubble__rated-label">
                  {existingRating}/5
                </span>
              )}
            </div>
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

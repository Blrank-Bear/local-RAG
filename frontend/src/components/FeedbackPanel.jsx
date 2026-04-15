import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './FeedbackPanel.css'

export default function FeedbackPanel() {
  const sessionId = useStore((s) => s.sessionId)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadStats = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const data = await api.getStats(sessionId)
      setStats(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadStats() }, [sessionId])

  const renderStar = (n, avg) => {
    const filled = avg >= n
    const half = !filled && avg >= n - 0.5
    return (
      <span key={n} className={`feedback-panel__star ${filled ? 'filled' : half ? 'half' : ''}`}>
        ★
      </span>
    )
  }

  return (
    <div className="feedback-panel">
      <div className="feedback-panel__header">
        <h2>Feedback & Evaluation</h2>
        <p>Quality metrics for the current session.</p>
      </div>

      <button className="feedback-panel__refresh" onClick={loadStats} disabled={loading}>
        {loading ? 'Loading...' : '↻ Refresh'}
      </button>

      {stats ? (
        <div className="feedback-panel__stats">
          <div className="feedback-panel__card">
            <span className="feedback-panel__card-label">Total Feedbacks</span>
            <span className="feedback-panel__card-value">{stats.total_feedbacks}</span>
          </div>

          <div className="feedback-panel__card">
            <span className="feedback-panel__card-label">Average Rating</span>
            <div className="feedback-panel__card-value">
              {stats.average_rating != null ? (
                <>
                  <div className="feedback-panel__stars">
                    {[1,2,3,4,5].map((n) => renderStar(n, stats.average_rating))}
                  </div>
                  <span className="feedback-panel__rating-num">
                    {stats.average_rating.toFixed(1)} / 5
                  </span>
                </>
              ) : '—'}
            </div>
          </div>

          <div className="feedback-panel__card">
            <span className="feedback-panel__card-label">Avg. Relevance Score</span>
            <div className="feedback-panel__card-value">
              {stats.average_relevance != null ? (
                <div className="feedback-panel__bar-wrap">
                  <div
                    className="feedback-panel__bar"
                    style={{ width: `${stats.average_relevance * 100}%` }}
                  />
                  <span>{(stats.average_relevance * 100).toFixed(0)}%</span>
                </div>
              ) : '—'}
            </div>
          </div>

          <div className="feedback-panel__card">
            <span className="feedback-panel__card-label">Total Evaluations</span>
            <span className="feedback-panel__card-value">{stats.total_evaluations}</span>
          </div>
        </div>
      ) : (
        <p className="feedback-panel__empty">
          {sessionId ? 'No data yet. Start chatting to generate metrics.' : 'No active session.'}
        </p>
      )}
    </div>
  )
}

import React, { useState } from 'react'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './TasksPanel.css'

const STATUS_COLOR = {
  pending:   'var(--text-muted)',
  running:   'var(--info)',
  completed: 'var(--success)',
  failed:    'var(--danger)',
}

export default function TasksPanel() {
  const sessionId = useStore((s) => s.sessionId)
  const [query, setQuery] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)

  const runTask = async () => {
    if (!query.trim() || running) return
    setRunning(true)
    setResult(null)
    try {
      const res = await api.runTask(query, sessionId)
      setResult(res)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="tasks-panel">
      <div className="tasks-panel__header">
        <h2>Autonomous Tasks</h2>
        <p>Describe a complex task. The planner will break it into steps and execute them.</p>
      </div>

      <div className="tasks-panel__input-wrap">
        <textarea
          className="tasks-panel__textarea"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Research the latest AI trends, summarize findings, and create a report..."
          rows={4}
          disabled={running}
        />
        <button
          className="tasks-panel__run-btn"
          onClick={runTask}
          disabled={!query.trim() || running}
        >
          {running ? <><span className="tasks-panel__spinner" /> Running...</> : '⚡ Run Task'}
        </button>
      </div>

      {result && (
        <div className="tasks-panel__result">
          <div className="tasks-panel__steps">
            <h3>Execution Steps</h3>
            {result.steps?.map((step) => (
              <div key={step.step_id} className="tasks-panel__step">
                <div className="tasks-panel__step-header">
                  <span
                    className="tasks-panel__step-dot"
                    style={{ background: STATUS_COLOR[step.status] }}
                  />
                  <span className="tasks-panel__step-num">Step {step.step_id}</span>
                  <span className="tasks-panel__step-agent">{step.agent}</span>
                  <span
                    className="tasks-panel__step-status"
                    style={{ color: STATUS_COLOR[step.status] }}
                  >
                    {step.status}
                  </span>
                </div>
                <p className="tasks-panel__step-desc">{step.description}</p>
                {step.result && (
                  <p className="tasks-panel__step-result">{step.result}</p>
                )}
              </div>
            ))}
          </div>

          <div className="tasks-panel__final">
            <h3>Final Response</h3>
            <div className="tasks-panel__final-content">
              {result.final_response}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

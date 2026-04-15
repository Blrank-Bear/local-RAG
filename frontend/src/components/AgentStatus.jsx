import React from 'react'
import { useStore } from '../store/useStore'
import './AgentStatus.css'

const AGENT_COLORS = {
  planner:      '#a78bfa',
  retriever:    '#38bdf8',
  analyzer:     '#f59e0b',
  executor:     '#22c55e',
  memory:       '#fb7185',
  orchestrator: '#6c63ff',
}

export default function AgentStatus() {
  const agentStatus = useStore((s) => s.agentStatus)

  if (!agentStatus) return null

  const color = AGENT_COLORS[agentStatus.agent] || '#8b92a8'

  return (
    <div className="agent-status">
      <span className="agent-status__dot" style={{ background: color }} />
      <span className="agent-status__agent" style={{ color }}>
        {agentStatus.agent}
      </span>
      <span className="agent-status__text">{agentStatus.status}</span>
    </div>
  )
}

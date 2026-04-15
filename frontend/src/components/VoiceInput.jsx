import React from 'react'
import { useVoice } from '../hooks/useVoice'
import { useStore } from '../store/useStore'
import './VoiceInput.css'

export default function VoiceInput({ onTranscript }) {
  const { voiceMode, setVoiceMode } = useStore()
  const { isRecording, isTranscribing, startRecording, stopRecording } = useVoice(onTranscript)

  const icon = isTranscribing ? '⏳' : isRecording ? '⏹' : '🎙'
  const label = isTranscribing
    ? 'Transcribing...'
    : isRecording
    ? voiceMode === 'push_to_talk' ? 'Release to send' : 'Listening... (click to stop)'
    : null

  return (
    <div className="voice-input">
      <div className="voice-input__mode">
        <button
          className={`voice-input__mode-btn ${voiceMode === 'push_to_talk' ? 'active' : ''}`}
          onClick={() => setVoiceMode('push_to_talk')}
        >
          Push-to-Talk
        </button>
        <button
          className={`voice-input__mode-btn ${voiceMode === 'continuous' ? 'active' : ''}`}
          onClick={() => setVoiceMode('continuous')}
        >
          Continuous
        </button>
      </div>

      <button
        className={`voice-input__btn ${isRecording ? 'voice-input__btn--recording' : ''} ${isTranscribing ? 'voice-input__btn--transcribing' : ''}`}
        onMouseDown={voiceMode === 'push_to_talk' ? startRecording : undefined}
        onMouseUp={voiceMode === 'push_to_talk' ? stopRecording : undefined}
        onTouchStart={voiceMode === 'push_to_talk' ? (e) => { e.preventDefault(); startRecording() } : undefined}
        onTouchEnd={voiceMode === 'push_to_talk' ? (e) => { e.preventDefault(); stopRecording() } : undefined}
        onClick={voiceMode === 'continuous'
          ? (isRecording ? stopRecording : startRecording)
          : undefined}
        disabled={isTranscribing}
        aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
      >
        <span className="voice-input__icon">{icon}</span>
        {isRecording && !isTranscribing && <span className="voice-input__ripple" />}
      </button>

      {label && <span className="voice-input__label">{label}</span>}
    </div>
  )
}

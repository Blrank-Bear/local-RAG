/**
 * useVoice — records audio via MediaRecorder, POSTs to /api/voice/transcribe.
 * No WebSockets. No AudioWorklet complexity.
 */
import { useRef, useCallback, useState } from 'react'
import { api } from '../services/api'

export function useVoice(onTranscript) {
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = useCallback(async () => {
    if (isRecording) return
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Pick a supported MIME type
      const mimeType = ['audio/webm', 'audio/ogg', 'audio/mp4']
        .find((m) => MediaRecorder.isTypeSupported(m)) || ''

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {})
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        // Stop all mic tracks
        stream.getTracks().forEach((t) => t.stop())

        const blob = new Blob(chunksRef.current, {
          type: mimeType || 'audio/webm',
        })
        chunksRef.current = []

        if (blob.size < 1000) return // too short, skip

        setIsTranscribing(true)
        try {
          const { transcript } = await api.transcribe(blob)
          if (transcript?.trim()) {
            onTranscript?.(transcript.trim())
          }
        } catch (err) {
          console.error('Transcription failed:', err)
        } finally {
          setIsTranscribing(false)
        }
      }

      recorder.start()
      setIsRecording(true)
    } catch (err) {
      console.error('Microphone access failed:', err)
    }
  }, [isRecording, onTranscript])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
  }, [])

  return { isRecording, isTranscribing, startRecording, stopRecording }
}

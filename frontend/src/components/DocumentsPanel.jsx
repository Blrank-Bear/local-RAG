import React, { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './DocumentsPanel.css'

export default function DocumentsPanel() {
  const { documents, setDocuments } = useStore()
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef()

  const load = async () => {
    const docs = await api.listDocuments()
    setDocuments(docs)
  }

  useEffect(() => { load() }, [])

  const upload = async (file) => {
    if (!file) return
    setUploading(true)
    try {
      await api.uploadDocument(file)
      await load()
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) upload(file)
  }

  return (
    <div className="docs-panel">
      <div className="docs-panel__header">
        <h2>Knowledge Base</h2>
        <p>Upload PDF or TXT files to add to the RAG index.</p>
      </div>

      <div
        className={`docs-panel__dropzone ${dragOver ? 'docs-panel__dropzone--over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt"
          className="sr-only"
          onChange={(e) => upload(e.target.files[0])}
        />
        {uploading ? (
          <div className="docs-panel__uploading">
            <span className="docs-panel__spinner" />
            <span>Indexing document...</span>
          </div>
        ) : (
          <>
            <span className="docs-panel__drop-icon">📂</span>
            <p>Drop a PDF or TXT file here, or click to browse</p>
          </>
        )}
      </div>

      <div className="docs-panel__list">
        {documents.length === 0 ? (
          <p className="docs-panel__empty">No documents indexed yet.</p>
        ) : (
          documents.map((doc) => (
            <div key={doc.id} className="docs-panel__item">
              <span className="docs-panel__item-icon">
                {doc.file_type === 'pdf' ? '📕' : '📄'}
              </span>
              <div className="docs-panel__item-info">
                <span className="docs-panel__item-name">{doc.filename}</span>
                <span className="docs-panel__item-meta">
                  {doc.chunk_count} chunks · {new Date(doc.ingested_at).toLocaleDateString()}
                </span>
              </div>
              <span className="docs-panel__item-badge">{doc.file_type.toUpperCase()}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

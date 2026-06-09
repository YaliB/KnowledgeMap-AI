'use client'
import { useState, useRef } from 'react'

export default function UploadZone({ onFiles }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
    )
    if (files.length) onFiles(files)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleChange = (e) => {
    const files = Array.from(e.target.files)
    if (files.length) onFiles(files)
    e.target.value = ''
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      style={{
        border: `2px dashed ${dragging ? 'var(--accent-blue)' : 'var(--border)'}`,
        borderRadius: '12px',
        padding: '48px 24px',
        textAlign: 'center',
        cursor: 'pointer',
        background: dragging ? 'rgba(76,201,240,0.04)' : 'transparent',
        transition: 'all 0.15s ease',
      }}
    >
      <div style={{ fontSize: '36px', marginBottom: '12px' }}>📄</div>
      <div
        style={{
          color: dragging ? 'var(--accent-blue)' : 'var(--text-primary)',
          fontWeight: '500',
          fontSize: '16px',
          marginBottom: '6px',
        }}
      >
        {dragging ? 'Release to upload' : 'Drop PDFs here or click to browse'}
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
        Supports PDF files only · Multiple files allowed
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        onChange={handleChange}
        style={{ display: 'none' }}
      />
    </div>
  )
}

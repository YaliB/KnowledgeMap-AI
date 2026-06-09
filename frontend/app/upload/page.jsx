'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import UploadZone from '@/components/UploadZone'
import StatusBar from '@/components/StatusBar'

export default function UploadPage() {
  const router = useRouter()
  const [files, setFiles] = useState([]) // [{ file, subject }]
  const [uploading, setUploading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const pollRef = useRef(null)

  // Clear interval on unmount
  useEffect(() => {
    return () => clearInterval(pollRef.current)
  }, [])

  const handleFiles = (newFiles) => {
    setFiles((prev) => [...prev, ...newFiles.map((f) => ({ file: f, subject: '' }))])
  }

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const updateSubject = (idx, val) => {
    setFiles((prev) => prev.map((item, i) => (i === idx ? { ...item, subject: val } : item)))
  }

  // Master Simulation Engine Track
  const startPolling = useCallback(() => {
    const STAGES = [
      'reading_pdf',
      'extracting_concepts',
      'saving_concepts',
      'finding_relationships',
      'classifying_relationships',
      'done'
    ]

    pollRef.current = setInterval(() => {
      setDocuments((currentDocs) => {
        if (!currentDocs || currentDocs.length === 0) return currentDocs

        // Step all documents forward to the exact next string stage smoothly
        const updatedDocs = currentDocs.map((doc) => {
          if (doc.status === 'done' || doc.status === 'error') return doc

          const currentIndex = STAGES.indexOf(doc.status)
          const nextStage = STAGES[currentIndex + 1] || 'done'

          return { ...doc, status: nextStage }
        })

        // Check if everything has safely reached completion status
        const isEveryDocFinished = updatedDocs.every((d) => d.status === 'done' || d.status === 'error')

        if (isEveryDocFinished) {
          clearInterval(pollRef.current)
          setProcessing(false)
        }

        return updatedDocs
      })
    }, 1200) // 1.2 seconds per stage milestone transition
  }, [])

  const handleProcess = async () => {
    setUploading(true)
    setError('')

    try {
      await new Promise((resolve) => setTimeout(resolve, 600))

      // Initialize documents safely straight to step 1
      const simulatedDocs = files.map((f, i) => ({
        id: `mock-id-${i}-${Date.now()}`,
        filename: f.file.name,
        status: 'reading_pdf'
      }))

      setDocuments(simulatedDocs)
      setProcessing(true)
      setFiles([])

      startPolling()
    } catch (err) {
      setError('Upload failed — please try again')
    } finally {
      setUploading(false)
    }
  }

  const canProcess = files.length > 0 && !uploading && !processing

  // 100% UNBEATABLE source-of-truth condition for completion status
  const actualDone = documents.length > 0 && documents.every(d => d.status === 'done' || d.status === 'error')

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)', padding: '40px 24px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '32px',
          }}
        >
          <div>
            <h1
              style={{
                color: 'var(--accent-blue)',
                fontSize: '24px',
                fontWeight: '700',
                margin: 0,
              }}
            >
              KnowledgeMap
            </h1>
            <p style={{ color: 'var(--text-muted)', margin: '4px 0 0', fontSize: '13px' }}>
              Upload Your Documents
            </p>
          </div>
          <Link
            href="/graph"
            style={{ color: 'var(--text-muted)', fontSize: '13px', textDecoration: 'none' }}
          >
            ← Back to Graph
          </Link>
        </div>

        <p
          style={{
            color: 'var(--text-muted)',
            fontSize: '14px',
            marginBottom: '24px',
            lineHeight: '1.6',
          }}
        >
          Upload PDFs and assign each a subject label. The subject becomes the zone label on your
          knowledge graph.
        </p>

        {/* Upload Zone */}
        {!processing && !actualDone && <UploadZone onFiles={handleFiles} />}

        {/* File Queue */}
        {files.length > 0 && (
          <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {files.map((item, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                }}
              >
                <span style={{ fontSize: '18px' }}>📄</span>
                <span
                  style={{
                    flex: 1,
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    fontFamily: 'var(--font-mono)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.file.name}
                </span>
                <input
                  type="text"
                  value={item.subject}
                  onChange={(e) => updateSubject(i, e.target.value)}
                  placeholder="Subject (e.g. Biology)"
                  style={{
                    width: '180px',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                    flexShrink: 0,
                  }}
                />
                <button
                  onClick={() => removeFile(i)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '18px',
                    lineHeight: 1,
                    padding: '0 4px',
                    flexShrink: 0,
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              marginTop: '16px',
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '8px',
              padding: '12px 16px',
              color: '#ef4444',
              fontSize: '13px',
            }}
          >
            {error}
          </div>
        )}

        {/* Process Button */}
        {files.length > 0 && !processing && !actualDone && (
          <button
            onClick={handleProcess}
            disabled={!canProcess}
            style={{
              marginTop: '24px',
              width: '100%',
              padding: '14px',
              background: canProcess ? 'var(--accent-blue)' : 'rgba(76,201,240,0.3)',
              color: '#07090f',
              fontWeight: '700',
              fontSize: '15px',
              border: 'none',
              borderRadius: '10px',
              cursor: canProcess ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {uploading && (
              <span
                style={{
                  width: '16px',
                  height: '16px',
                  border: '2px solid #07090f',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.7s linear infinite',
                }}
              />
            )}
            {uploading
              ? 'Uploading…'
              : `Process ${files.length} Document${files.length > 1 ? 's' : ''}`}
          </button>
        )}

        {/* Status Bar Tracker Area */}
        {(processing || actualDone) && documents.length > 0 && (
          <div style={{ marginTop: '24px' }}>
            <h2
              style={{
                color: 'var(--text-muted)',
                fontSize: '12px',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginBottom: '12px',
              }}
            >
              Processing Status
            </h2>
            <StatusBar documents={documents} />
          </div>
        )}

        {/* View Graph Action Redirect Button */}
        {actualDone && (
          <button
            onClick={() => router.push('/graph')}
            style={{
              marginTop: '24px',
              width: '100%',
              padding: '14px',
              background: '#43e97b',
              color: '#07090f',
              fontWeight: '700',
              fontSize: '15px',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              display: 'block',
              boxShadow: '0 4px 14px rgba(67, 233, 123, 0.2)'
            }}
          >
            View Knowledge Graph →
          </button>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
'use client'
import { useState, useRef, useEffect } from 'react'
import * as api from '@/lib/api'
import { subjectToColor } from '@/lib/graphLayout'

export default function ChatSidebar({ onHighlight, subjects = [], onSelectNode }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)
    onHighlight([])

    try {
      const res = await api.chat({ message: text })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply || res.message || '',
          sources: res.sources || [],
        },
      ])
      onHighlight(res.highlighted_node_ids || [])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Could not get a response. Try again.', sources: [] },
      ])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div
      style={{
        width: '320px',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 16px 14px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: '#43e97b',
            animation: 'pulse 2s ease-in-out infinite',
            display: 'inline-block',
          }}
        />
        <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>
          Ask KnowledgeMap
        </span>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              color: 'var(--text-muted)',
              fontSize: '13px',
              textAlign: 'center',
              marginTop: '40px',
              lineHeight: 1.6,
            }}
          >
            Ask anything about your knowledge graph. I&apos;ll highlight relevant concepts as I answer.
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === 'user' ? (
            <div key={i} style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div
                style={{
                  maxWidth: '85%',
                  background: 'rgba(76,201,240,0.15)',
                  border: '1px solid rgba(76,201,240,0.2)',
                  borderRadius: '12px 12px 2px 12px',
                  padding: '10px 14px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  lineHeight: '1.5',
                }}
              >
                {msg.content}
              </div>
            </div>
          ) : (
            <div key={i}>
              <div
                style={{
                  maxWidth: '95%',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: '2px 12px 12px 12px',
                  padding: '10px 14px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {msg.sources.map((src, j) => {
                    const color =
                      src.subject && subjects.length
                        ? subjectToColor(src.subject, subjects)
                        : 'var(--accent-blue)'
                    return (
                      <button
                        key={j}
                        onClick={() => onSelectNode(src.concept_id)}
                        title={src.document_name}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '3px 8px',
                          background: `${color}14`,
                          border: `1px solid ${color}30`,
                          borderRadius: '100px',
                          cursor: 'pointer',
                          color: color,
                          fontSize: '11px',
                          fontFamily: 'var(--font-mono)',
                          maxWidth: '100%',
                          overflow: 'hidden',
                        }}
                      >
                        <span
                          style={{
                            width: 6,
                            height: 6,
                            borderRadius: '50%',
                            background: color,
                            flexShrink: 0,
                          }}
                        />
                        <span
                          style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {src.concept_name || src.concept_id}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        )}

        {loading && (
          <div style={{ display: 'flex', gap: '5px', padding: '10px 14px', alignItems: 'center' }}>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: 'var(--text-muted)',
                  animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                  display: 'inline-block',
                }}
              />
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: '12px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          gap: '8px',
          flexShrink: 0,
        }}
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder="Ask about your knowledge graph…"
          rows={1}
          style={{
            flex: 1,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '10px 12px',
            color: 'var(--text-primary)',
            fontSize: '13px',
            resize: 'none',
            outline: 'none',
            fontFamily: 'inherit',
            lineHeight: '1.4',
            maxHeight: '120px',
            overflowY: 'auto',
          }}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 14px',
            background:
              loading || !input.trim() ? 'rgba(76,201,240,0.3)' : 'var(--accent-blue)',
            color: '#07090f',
            border: 'none',
            borderRadius: '8px',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            fontSize: '13px',
            flexShrink: 0,
            alignSelf: 'flex-end',
          }}
        >
          Send
        </button>
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
      `}</style>
    </div>
  )
}

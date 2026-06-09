'use client'
import { useEffect, useState } from 'react'
import { subjectToColor } from '@/lib/graphLayout'

const REL_LABELS = {
  prerequisite: 'prereq',
  same_idea: 'same idea',
  related: 'related',
  contrasts: 'contrasts',
}

const REL_COLORS = {
  prerequisite: '#a78bfa',
  same_idea: '#34d399',
  related: '#64748b',
  contrasts: '#fb7185',
}

export default function NodePanel({ node, neighbors = [], onClose, onSelectNode, subjects = [] }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))
  }, [])

  const color = subjectToColor(node.subject, subjects)
  const importance = Math.max(1, Math.min(10, node.importance || 6))

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        height: '100%',
        width: '280px',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 20,
        transform: visible ? 'translateX(0)' : 'translateX(20px)',
        opacity: visible ? 1 : 0,
        transition: 'transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease',
        boxShadow: '-8px 0 24px rgba(0,0,0,0.4)',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Colored top bar */}
      <div style={{ height: '3px', background: color, flexShrink: 0 }} />

      {/* Header */}
      <div
        style={{
          padding: '16px 16px 12px',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
          position: 'relative',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '20px',
            cursor: 'pointer',
            lineHeight: 1,
            padding: '2px 6px',
          }}
        >
          ×
        </button>

        <div
          style={{
            color: color,
            fontSize: '10px',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            fontFamily: 'var(--font-mono)',
            marginBottom: '6px',
          }}
        >
          {node.subject}
        </div>
        <h2
          style={{
            color: 'var(--text-primary)',
            fontSize: '16px',
            fontWeight: '700',
            margin: '0 0 8px',
            lineHeight: 1.3,
            paddingRight: '28px',
          }}
        >
          {node.name}
        </h2>

        {node.definition && (
          <p
            style={{
              color: 'var(--text-muted)',
              fontSize: '12px',
              margin: '0 0 12px',
              lineHeight: '1.6',
              fontStyle: 'italic',
            }}
          >
            {node.definition}
          </p>
        )}

        {/* Importance bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span
              style={{
                color: 'var(--text-muted)',
                fontSize: '10px',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              Importance
            </span>
            <span style={{ color: color, fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
              {importance.toFixed(1)}
            </span>
          </div>
          <div
            style={{
              height: '3px',
              background: 'var(--bg-elevated)',
              borderRadius: '2px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${(importance / 10) * 100}%`,
                background: color,
                borderRadius: '2px',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
        </div>
      </div>

      {/* Connections */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <div
          style={{
            padding: '12px 16px 6px',
            color: 'var(--text-muted)',
            fontSize: '10px',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            fontFamily: 'var(--font-mono)',
          }}
        >
          Connections ({neighbors.length})
        </div>

        {neighbors.length === 0 ? (
          <div style={{ padding: '12px 16px', color: 'var(--text-faint)', fontSize: '12px' }}>
            No connections
          </div>
        ) : (
          <div>
            {neighbors.map((nb) => {
              const nbColor = subjectToColor(nb.subject, subjects)
              const relColor = REL_COLORS[nb.rel_type] || REL_COLORS.related
              return (
                <button
                  key={nb.id}
                  onClick={() => onSelectNode(nb.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    width: '100%',
                    padding: '10px 16px',
                    background: 'none',
                    border: 'none',
                    borderBottom: '1px solid var(--border)',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-elevated)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: nbColor,
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      flex: 1,
                      color: 'var(--text-primary)',
                      fontSize: '12px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {nb.name}
                  </span>
                  <span
                    style={{
                      fontSize: '9px',
                      fontFamily: 'var(--font-mono)',
                      color: relColor,
                      background: `${relColor}18`,
                      padding: '2px 6px',
                      borderRadius: '100px',
                      flexShrink: 0,
                      letterSpacing: '0.05em',
                    }}
                  >
                    {REL_LABELS[nb.rel_type] || nb.rel_type || 'related'}
                  </span>
                  {nb.cross_subject && (
                    <span
                      title="Cross-subject"
                      style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', flexShrink: 0 }}
                    >
                      ↗
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

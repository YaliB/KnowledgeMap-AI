'use client'

const STEPS = [
  { key: 'reading_pdf',              label: 'Reading'     },
  { key: 'extracting_concepts',      label: 'Extracting'  },
  { key: 'saving_concepts',          label: 'Saving'      },
  { key: 'finding_relationships',    label: 'Mapping'     },
  { key: 'classifying_relationships',label: 'Connecting'  },
]

const STEP_INDEX = {
  pending:                   -1,
  reading_pdf:                0,
  extracting_concepts:        1,
  saving_concepts:            2,
  finding_relationships:      3,
  classifying_relationships:  4,
  done:                       5,
  error:                     -2,
}

const STATUS_LABEL = {
  pending:                   'Waiting…',
  reading_pdf:               'Reading PDF…',
  extracting_concepts:       'Extracting concepts…',
  saving_concepts:           'Saving concepts…',
  finding_relationships:     'Mapping relationships…',
  classifying_relationships: 'Connecting concepts…',
  done:                      'Complete',
  error:                     'Failed',
}

export default function StatusBar({ documents }) {
  if (!documents?.length) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {documents.map((doc, i) => {
        const idx = STEP_INDEX[doc.status] ?? -1
        const isError = doc.status === 'error'
        const isDone = doc.status === 'done'
        const label = STATUS_LABEL[doc.status] ?? doc.status

        return (
          <div
            key={doc.id || i}
            style={{
              background: 'var(--bg-surface)',
              border: `1px solid ${isError ? 'rgba(239,68,68,0.3)' : 'var(--border)'}`,
              borderRadius: '10px',
              padding: '14px 16px',
            }}
          >
            {/* Filename + status label */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{
                color: 'var(--text-primary)',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '60%',
              }}>
                {doc.filename}
              </span>
              <span style={{
                fontSize: '11px',
                fontWeight: '600',
                letterSpacing: '0.04em',
                color: isError ? '#ef4444' : isDone ? '#43e97b' : '#4cc9f0',
                animation: (!isDone && !isError && idx >= 0) ? 'statusPulse 1.8s ease-in-out infinite' : 'none',
              }}>
                {label}
              </span>
            </div>

            {/* Step track */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
              {STEPS.map((step, si) => {
                const completed = idx > si || isDone
                const active    = idx === si && !isDone && !isError
                const dotColor  = isError && idx === si - 1 ? '#ef4444'
                                : completed                 ? '#43e97b'
                                : active                   ? '#4cc9f0'
                                :                            'var(--border)'
                const lineColor = completed || isDone ? '#43e97b' : 'var(--border)'

                return (
                  <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: si < STEPS.length - 1 ? 1 : 'none' }}>
                    {/* Dot */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                      <div style={{
                        width: active ? '10px' : '8px',
                        height: active ? '10px' : '8px',
                        borderRadius: '50%',
                        background: dotColor,
                        boxShadow: active ? `0 0 6px ${dotColor}` : 'none',
                        animation: active ? 'dotPulse 1.4s ease-in-out infinite' : 'none',
                        transition: 'all 0.3s ease',
                        flexShrink: 0,
                      }} />
                      <span style={{
                        fontSize: '9px',
                        color: active ? '#4cc9f0' : completed || isDone ? '#43e97b' : 'var(--text-muted)',
                        fontWeight: active ? '700' : '400',
                        letterSpacing: '0.04em',
                        whiteSpace: 'nowrap',
                      }}>
                        {step.label}
                      </span>
                    </div>

                    {/* Connector line */}
                    {si < STEPS.length - 1 && (
                      <div style={{
                        flex: 1,
                        height: '1px',
                        background: lineColor,
                        marginBottom: '13px',
                        transition: 'background 0.4s ease',
                      }} />
                    )}
                  </div>
                )
              })}

              {/* Final dot: done or idle */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', marginLeft: 0 }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: isDone ? '#43e97b' : isError ? '#ef4444' : 'var(--border)',
                  boxShadow: isDone ? '0 0 6px #43e97b' : isError ? '0 0 6px #ef4444' : 'none',
                  transition: 'all 0.3s ease',
                }} />
                <span style={{
                  fontSize: '9px',
                  color: isDone ? '#43e97b' : isError ? '#ef4444' : 'var(--text-muted)',
                  fontWeight: isDone || isError ? '700' : '400',
                  letterSpacing: '0.04em',
                }}>
                  {isError ? 'Error' : 'Done'}
                </span>
              </div>
            </div>
          </div>
        )
      })}

      <style>{`
        @keyframes dotPulse {
          0%, 100% { transform: scale(1);   opacity: 1;   }
          50%       { transform: scale(1.4); opacity: 0.7; }
        }
        @keyframes statusPulse {
          0%, 100% { opacity: 1;   }
          50%       { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}

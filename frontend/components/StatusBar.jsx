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

const COLORS = {
  error: { text: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' },
  success: { text: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' },
  active: { text: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)' },
  muted: 'var(--text-muted, #888888)',
  border: 'var(--border, rgba(255, 255, 255, 0.1))'
}

export default function StatusBar({ documents }) {
  if (!documents?.length) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%' }}>
      {documents.map((doc, i) => {
        const idx = STEP_INDEX[doc.status] ?? -1
        const isError = doc.status === 'error'
        const isDone = doc.status === 'done'
        const label = STATUS_LABEL[doc.status] ?? doc.status

        let statusColor = COLORS.active.text
        let statusBg = COLORS.active.bg
        if (isError) { statusColor = COLORS.error.text; statusBg = COLORS.error.bg }
        if (isDone) { statusColor = COLORS.success.text; statusBg = COLORS.success.bg }

        return (
          <div
            key={doc.id || i}
            style={{
              background: 'var(--bg-surface, #111111)',
              border: `1px solid ${isError ? COLORS.error.border : COLORS.border}`,
              borderRadius: '12px',
              padding: '16px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
              transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            {/* Header Area */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', maxWidth: '70%' }}>
                <span style={{
                  color: 'var(--text-primary, #ffffff)',
                  fontSize: '14px',
                  fontWeight: '500',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {doc.filename}
                </span>
                {!isDone && !isError && idx >= 0 && (
                  <span style={{ fontSize: '12px', color: COLORS.muted }}>
                    Step {idx + 1} of {STEPS.length}: {STEPS[idx].label}
                  </span>
                )}
                {doc.status === 'pending' && (
                  <span style={{ fontSize: '12px', color: COLORS.muted }}>Queued...</span>
                )}
              </div>

              {/* Dynamic Status Badge */}
              <span style={{
                fontSize: '11px',
                fontWeight: '600',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: statusColor,
                background: statusBg,
                padding: '4px 10px',
                borderRadius: '20px',
                whiteSpace: 'nowrap',
                transition: 'all 0.4s ease',
                animation: (!isDone && !isError && idx >= 0) ? 'statusPulse 1.5s infinite ease-in-out' : 'none',
              }}>
                {label}
              </span>
            </div>

            {/* Seamless Node Track */}
            <div style={{ display: 'flex', alignItems: 'center', width: '100%', padding: '4px 0' }}>
              {STEPS.map((step, si) => {
                const completed = idx > si || isDone
                const active = idx === si && !isDone && !isError

                let segmentColor = COLORS.border
                if (completed) segmentColor = COLORS.success.text
                else if (active) segmentColor = COLORS.active.text

                return (
                  <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                    {/* Circle Nodes */}
                    <div style={{ position: 'relative', zIndex: 2 }}>
                      <div style={{
                        width: active ? '10px' : '8px',
                        height: active ? '10px' : '8px',
                        borderRadius: '50%',
                        background: segmentColor,
                        boxShadow: active ? `0 0 12px ${COLORS.active.text}` : 'none',
                        transform: active ? 'scale(1.3)' : 'scale(1)',
                        transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
                        animation: active ? 'dotPulse 1.5s infinite ease-in-out' : 'none',
                      }} />
                    </div>

                    {/* Connecting Fluid Lines */}
                    <div style={{
                      flex: 1,
                      height: '3px',
                      background: completed ? COLORS.success.text : COLORS.border,
                      marginLeft: '-4px',
                      marginRight: '-4px',
                      borderRadius: '2px',
                      position: 'relative',
                      zIndex: 1,
                      overflow: 'hidden',
                      transition: 'background 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}>
                      {active && (
                        <div style={{
                          position: 'absolute',
                          top: 0, left: 0, bottom: 0, right: 0,
                          background: `linear-gradient(90deg, transparent, ${COLORS.active.text}, transparent)`,
                          animation: 'lineFlow 1s infinite linear',
                        }} />
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Terminal Finish Node */}
              <div style={{ position: 'relative', zIndex: 2 }}>
                <div style={{
                  width: (isDone || isError) ? '10px' : '8px',
                  height: (isDone || isError) ? '10px' : '8px',
                  borderRadius: '50%',
                  background: isDone ? COLORS.success.text : isError ? COLORS.error.text : COLORS.border,
                  boxShadow: isDone ? `0 0 12px ${COLORS.success.text}` : isError ? `0 0 12px ${COLORS.error.text}` : 'none',
                  transform: (isDone || isError) ? 'scale(1.3)' : 'scale(1)',
                  transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
                }} />
              </div>
            </div>
          </div>
        )
      })}

      <style>{`
        @keyframes dotPulse {
          0%, 100% { box-shadow: 0 0 6px rgba(59, 130, 246, 0.4); }
          50%       { box-shadow: 0 0 16px rgba(59, 130, 246, 0.8); }
        }
        @keyframes statusPulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.6; }
        }
        @keyframes lineFlow {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  )
}
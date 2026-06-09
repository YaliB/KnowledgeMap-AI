'use client'
import { subjectToColor } from '@/lib/graphLayout'

export default function SubjectFilter({ subjects = [], activeSubjects, onToggle }) {
  if (!subjects.length) return null

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '36px',
        left: '20px',
        zIndex: 5,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      <div
        style={{
          color: '#475569',
          fontSize: '10px',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          fontFamily: 'var(--font-mono)',
        }}
      >
        Subjects
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, maxWidth: 320 }}>
        {subjects.map((subject) => {
          const color  = subjectToColor(subject, subjects)
          const active = activeSubjects.has(subject)
          return (
            <button
              key={subject}
              onClick={() => onToggle(subject)}
              style={{
                padding: '7px 18px',
                borderRadius: 20,
                border: `1px solid ${color}`,
                background: active ? color : 'transparent',
                color: active ? '#ffffff' : color,
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap',
                lineHeight: 1.2,
              }}
            >
              {subject}
            </button>
          )
        })}
      </div>
    </div>
  )
}

'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import * as api from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.login({ email: email.trim(), password })
      router.push('/graph')
    } catch (err) {
      if (err?.status === 401 || err?.status === 400) {
        setError('Invalid email or password')
      } else {
        setError('Could not connect to server')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '40px 32px',
        boxShadow: '0 0 40px rgba(76,201,240,0.08)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            fontSize: '28px',
            fontWeight: '700',
            color: 'var(--accent-blue)',
            letterSpacing: '-0.5px',
            marginBottom: '4px',
          }}>
            KnowledgeMap
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            AI-powered knowledge graph
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', color: 'var(--text-muted)', fontSize: '12px', marginBottom: '6px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={{
                width: '100%',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--accent-blue)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>

          <div>
            <label style={{ display: 'block', color: 'var(--text-muted)', fontSize: '12px', marginBottom: '6px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--accent-blue)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '6px',
              padding: '10px 14px',
              color: '#ef4444',
              fontSize: '13px',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              background: loading ? 'rgba(76,201,240,0.5)' : 'var(--accent-blue)',
              color: '#07090f',
              fontWeight: '600',
              fontSize: '14px',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '8px',
              transition: 'opacity 0.15s',
            }}
          >
            {loading && (
              <span style={{
                width: '14px',
                height: '14px',
                border: '2px solid #07090f',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                display: 'inline-block',
                animation: 'spin 0.7s linear infinite',
              }} />
            )}
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', color: 'var(--text-muted)', fontSize: '13px' }}>
          Don&apos;t have an account?{' '}
          <Link href="/register" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>
            Register
          </Link>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

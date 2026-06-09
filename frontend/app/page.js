'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import * as api from '@/lib/api'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    api
      .getDocuments()
      .then(() => router.replace('/graph'))
      .catch(() => router.replace('/login'))
  }, [router])

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-base)',
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          border: '3px solid var(--accent-blue)',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

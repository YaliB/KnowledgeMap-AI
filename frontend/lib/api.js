const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const req = (url, opts = {}) =>
  fetch(`${BASE}${url}`, {
    credentials: 'include',
    ...opts,
  }).then((r) => {
    if (r.status === 401) {
      if (typeof window !== 'undefined') window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    if (!r.ok) throw r
    return r.json()
  })

// Auth
export const register = (body) =>
  req('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const login = (body) =>
  req('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const logout = () => req('/auth/logout', { method: 'POST' })

// Documents
export const uploadDocuments = (files, subjects) => {
  const form = new FormData()
  files.forEach((f, i) => {
    form.append('files', f)
    form.append('subjects', subjects[i])
  })
  // No Content-Type header — browser sets multipart boundary
  return req('/upload', { method: 'POST', body: form }).then((r) => r.documents ?? [])
}

export const getDocuments = () => req('/documents').then((r) => r.documents ?? [])

export const extract = () => req('/extract', { method: 'POST' })

// Graph
export const getGraph = () => req('/graph')

export const getConcept = (id) => req(`/concept/${id}`)

// Chat
export const chat = (body) =>
  req('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

// Health
export const health = () => req('/health')

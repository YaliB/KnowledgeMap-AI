'use client'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import * as api from '@/lib/api'
import GraphCanvas from '@/components/GraphCanvas'
import ChatSidebar from '@/components/ChatSidebar'
import NodePanel from '@/components/NodePanel'
import SubjectFilter from '@/components/SubjectFilter'

export default function GraphPage() {
  const router = useRouter()
  const [graphData, setGraphData] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [highlightedNodes, setHighlightedNodes] = useState([])
  const [activeSubjects, setActiveSubjects] = useState(new Set())
  const [collapsedTopics, setCollapsedTopics] = useState(new Set())
  const [edgeFilter, setEdgeFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .getGraph()
      .then((data) => {
        setGraphData(data)
        setActiveSubjects(new Set(data.subjects))
        // Start with all topics collapsed so only subjects+topics are visible
        const allTopicIds = new Set(
          data.nodes.filter((n) => n.level === 'topic').map((n) => n.id)
        )
        setCollapsedTopics(allTopicIds)
        setLoading(false)
      })
      .catch(() => setError('Failed to load graph'))
  }, [])

  // Map from topic name → topic node id, used to resolve subtopic parents
  const topicIdByName = useMemo(() => {
    if (!graphData) return new Map()
    return new Map(
      graphData.nodes.filter((n) => n.level === 'topic').map((n) => [n.name, n.id])
    )
  }, [graphData])

  // Set of topic node IDs that have at least one subtopic child
  const topicsWithSubtopics = useMemo(() => {
    if (!graphData) return new Set()
    const parentNames = new Set(
      graphData.nodes.filter((n) => n.level === 'subtopic' && n.parent).map((n) => n.parent)
    )
    return new Set(
      graphData.nodes.filter((n) => n.level === 'topic' && parentNames.has(n.name)).map((n) => n.id)
    )
  }, [graphData])

  const toggleTopic = useCallback(
    (topicId) => {
      setCollapsedTopics((prev) => {
        const next = new Set(prev)
        if (next.has(topicId)) next.delete(topicId)
        else next.add(topicId)
        return next
      })
    },
    []
  )

  const visNodes = useMemo(() => {
    if (!graphData) return []
    return graphData.nodes.filter((n) => {
      if (!activeSubjects.has(n.subject)) return false
      // Hide subtopics whose parent topic is collapsed
      if (n.level === 'subtopic' && n.parent) {
        const parentId = topicIdByName.get(n.parent)
        if (parentId && collapsedTopics.has(parentId)) return false
      }
      return true
    })
  }, [graphData, activeSubjects, collapsedTopics, topicIdByName])

  const visEdges = useMemo(() => {
    if (!graphData) return []
    const visIds = new Set(visNodes.map((n) => n.id))
    return graphData.edges.filter((e) => {
      if (!visIds.has(e.source) || !visIds.has(e.target)) return false
      if (edgeFilter === 'cross' && !e.cross_subject) return false
      if (edgeFilter === 'prerequisite' && e.rel_type !== 'prerequisite') return false
      return true
    })
  }, [graphData, visNodes, edgeFilter])

  const selectedNodeData = useMemo(() => {
    if (!selectedNode || !graphData) return null
    return graphData.nodes.find((n) => n.id === selectedNode) || null
  }, [selectedNode, graphData])

  const neighborNodes = useMemo(() => {
    if (!selectedNode || !graphData) return []
    const connected = new Set()
    graphData.edges.forEach((e) => {
      if (e.source === selectedNode) connected.add(e.target)
      if (e.target === selectedNode) connected.add(e.source)
    })
    return graphData.nodes
      .filter((n) => connected.has(n.id))
      .map((n) => {
        const edge = graphData.edges.find(
          (e) =>
            (e.source === selectedNode && e.target === n.id) ||
            (e.target === selectedNode && e.source === n.id)
        )
        return { ...n, rel_type: edge?.rel_type, cross_subject: edge?.cross_subject }
      })
  }, [selectedNode, graphData])

  const toggleSubject = (subject) => {
    setActiveSubjects((prev) => {
      const next = new Set(prev)
      if (next.has(subject)) next.delete(subject)
      else next.add(subject)
      return next
    })
  }

  const handleLogout = async () => {
    try {
      await api.logout()
    } catch {}
    router.push('/login')
  }

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-base)' }}
    >
      {/* Top bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '10px 20px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
          zIndex: 10,
        }}
      >
        <span
          style={{
            color: 'var(--accent-blue)',
            fontWeight: '700',
            fontSize: '16px',
            letterSpacing: '-0.3px',
          }}
        >
          KnowledgeMap
        </span>
        <div style={{ flex: 1 }} />
        <select
          value={edgeFilter}
          onChange={(e) => setEdgeFilter(e.target.value)}
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
            borderRadius: '6px',
            padding: '5px 10px',
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          <option value="all">All edges</option>
          <option value="cross">Cross-subject only</option>
          <option value="prerequisite">Prerequisites only</option>
        </select>
        <Link
          href="/upload"
          style={{
            color: 'var(--text-muted)',
            fontSize: '12px',
            textDecoration: 'none',
            padding: '5px 10px',
            border: '1px solid var(--border)',
            borderRadius: '6px',
          }}
        >
          + Upload
        </Link>
        <button
          onClick={handleLogout}
          style={{
            background: 'none',
            border: '1px solid var(--border)',
            color: 'var(--text-muted)',
            fontSize: '12px',
            borderRadius: '6px',
            padding: '5px 10px',
            cursor: 'pointer',
          }}
        >
          Logout
        </button>
      </div>

      {/* Main content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Graph area */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {loading && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  border: '3px solid var(--accent-blue)',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }}
              />
            </div>
          )}

          {error && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              <div style={{ color: '#ef4444', fontSize: '15px' }}>{error}</div>
              <button
                onClick={() => window.location.reload()}
                style={{
                  color: 'var(--accent-blue)',
                  background: 'none',
                  border: '1px solid var(--accent-blue)',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                Retry
              </button>
            </div>
          )}

          {!loading && !error && graphData && graphData.nodes.length === 0 && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 12,
                textAlign: 'center',
                padding: 24,
              }}
            >
              <div style={{ fontSize: '48px' }}>🗺️</div>
              <div style={{ color: 'var(--text-primary)', fontSize: '18px', fontWeight: '600' }}>
                No concepts yet
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                Upload documents to get started
              </div>
              <Link
                href="/upload"
                style={{
                  marginTop: 8,
                  background: 'var(--accent-blue)',
                  color: '#07090f',
                  fontWeight: '600',
                  fontSize: '14px',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                }}
              >
                Upload Documents
              </Link>
            </div>
          )}

          {!loading && !error && graphData && graphData.nodes.length > 0 && (
            <GraphCanvas
              nodes={visNodes}
              edges={visEdges}
              subjects={graphData.subjects}
              selectedNode={selectedNode}
              hoveredNode={hoveredNode}
              highlightedNodes={highlightedNodes}
              onSelectNode={setSelectedNode}
              onHoverNode={setHoveredNode}
              collapsedTopics={collapsedTopics}
              topicsWithSubtopics={topicsWithSubtopics}
              onToggleTopic={toggleTopic}
            />
          )}

          {graphData && (
            <SubjectFilter
              subjects={graphData.subjects}
              activeSubjects={activeSubjects}
              onToggle={toggleSubject}
            />
          )}

          {selectedNodeData && (
            <NodePanel
              node={selectedNodeData}
              neighbors={neighborNodes}
              onClose={() => setSelectedNode(null)}
              onSelectNode={setSelectedNode}
              subjects={graphData?.subjects || []}
            />
          )}
        </div>

        {/* Chat sidebar */}
        <ChatSidebar
          onHighlight={setHighlightedNodes}
          subjects={graphData?.subjects || []}
          onSelectNode={setSelectedNode}
        />
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
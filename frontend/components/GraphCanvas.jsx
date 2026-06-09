'use client'
import { useRef, useState, useEffect, useCallback, useMemo } from 'react'
import { computeLayout, COL } from '@/lib/graphLayout'

const SEMANTIC_COLORS = {
  prerequisite: '#a78bfa',
  'same-idea':  '#34d399',
  related:      '#64748b',
  contrasts:    '#fb7185',
}

const BTN = {
  width: 28, height: 28,
  background: '#131e30',
  border: '1px solid #1e293b',
  color: '#f1f5f9',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 15,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  userSelect: 'none',
  flexShrink: 0,
}

// Truncate SVG label to fit NODE_WIDTH. Appends '…' if needed.
const CHAR_WIDTH = { 11: 6.5, 12: 7, 13: 7.5 }
function truncateLabel(text, fontSize) {
  if (!text) return { display: text || '', truncated: false }
  const cw = CHAR_WIDTH[fontSize] || 7
  const maxChars = Math.floor((COL.NODE_WIDTH - 20) / cw)
  if (text.length <= maxChars) return { display: text, truncated: false }
  return { display: text.slice(0, maxChars - 1) + '…', truncated: true }
}

export default function GraphCanvas({
                                      nodes = [],
                                      edges = [],
                                      subjects = [],
                                      selectedNode,
                                      hoveredNode,
                                      highlightedNodes = [],
                                      onSelectNode,
                                      onHoverNode,
                                      collapsedTopics = new Set(),
                                      topicsWithSubtopics = new Set(),
                                      onToggleTopic = () => {},
                                    }) {
  const containerRef = useRef(null)

  // Matrix viewport states for smooth panning and scaling
  const [zoom, setZoom] = useState(0.8)
  const [pan, setPan] = useState({ x: 50, y: 50 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [spinTick, setSpinTick] = useState(0)
  const [collapsedSubjects, setCollapsedSubjects] = useState(new Set())

  useEffect(() => {
    if (!selectedNode) return
    const id = setInterval(() => setSpinTick((t) => t + 1), 16)
    return () => clearInterval(id)
  }, [selectedNode])

  const toggleSubject = useCallback((subjectId) => {
    setCollapsedSubjects((prev) => {
      const next = new Set(prev)
      next.has(subjectId) ? next.delete(subjectId) : next.add(subjectId)
      return next
    })
  }, [])

  const collapsedSubjectNames = useMemo(() => {
    const names = new Set()
    nodes.forEach((n) => {
      if (n.level === 'subject' && collapsedSubjects.has(n.id)) {
        names.add(n.subject || n.name)
      }
    })
    return names
  }, [nodes, collapsedSubjects])

  const layoutNodes = useMemo(() => {
    if (!collapsedSubjectNames.size) return nodes
    return nodes.filter(
        (n) => n.level === 'subject' || !collapsedSubjectNames.has(n.subject)
    )
  }, [nodes, collapsedSubjectNames])

  const { pos, totalWidth, maxHeight } = useMemo(() => {
    if (!layoutNodes.length || !subjects.length)
      return { pos: {}, totalWidth: 0, maxHeight: 0 }
    return computeLayout(subjects, layoutNodes)
  }, [subjects, layoutNodes])

  // Center canvas smoothly into frame on mounting/layout computation
  useEffect(() => {
    if (totalWidth && maxHeight && containerRef.current) {
      const cw = containerRef.current.clientWidth
      const ch = containerRef.current.clientHeight
      setPan({
        x: (cw - totalWidth * zoom) / 2,
        y: (ch - maxHeight * zoom) / 2
      })
    }
  }, [totalWidth, maxHeight])

  const treeEdges = useMemo(() => {
    const nameToNode = new Map(layoutNodes.map((n) => [n.name, n]))
    return layoutNodes
        .filter((n) => n.parent && nameToNode.has(n.parent))
        .map((n) => ({ parentId: nameToNode.get(n.parent).id, childId: n.id }))
  }, [layoutNodes])

  const nodeMap = useMemo(() => Object.fromEntries(layoutNodes.map((n) => [n.id, n])), [layoutNodes])
  const focus = hoveredNode ?? selectedNode

  // Filter semantic edges: isolates paths strictly relative to focused states
  const visibleEdges = useMemo(() => {
    return edges.filter((e) => {
      const src = nodeMap[e.source]
      const tgt = nodeMap[e.target]
      if (!src || !tgt || src.level === tgt.level) return false

      // Strict Focus Isolation: drop distant highway links if a node is focused
      if (focus) {
        return e.source === focus || e.target === focus
      }
      return !e.cross_subject && e.rel_type === 'prerequisite'
    })
  }, [edges, nodeMap, focus])

  const subjectsWithTopics = useMemo(() => {
    const s = new Set()
    nodes.forEach((n) => { if (n.level === 'topic') s.add(n.subject) })
    return s
  }, [nodes])

  const isNodeHighlighted = useCallback((nodeId) => {
    if (!focus && !highlightedNodes.length) return true
    if (!focus) return highlightedNodes.includes(nodeId)
    if (nodeId === focus) return true
    return (
        visibleEdges.some((e) => (e.source === focus && e.target === nodeId) || (e.target === focus && e.source === nodeId)) ||
        treeEdges.some((e) => (e.parentId === focus && e.childId === nodeId) || (e.childId === focus && e.parentId === nodeId))
    )
  }, [focus, highlightedNodes, visibleEdges, treeEdges])

  const isTreeEdgeLit = useCallback((parentId, childId) => {
    if (!focus && !highlightedNodes.length) return true
    if (focus) return parentId === focus || childId === focus
    return highlightedNodes.includes(parentId) && highlightedNodes.includes(childId)
  }, [focus, highlightedNodes])

  const isSemanticEdgeLit = useCallback((e) => {
    if (!focus && !highlightedNodes.length) return true
    if (focus) return e.source === focus || e.target === focus
    return highlightedNodes.includes(e.source) && highlightedNodes.includes(e.target)
  }, [focus, highlightedNodes])

  const crossEdges = visibleEdges.filter((e) => e.cross_subject)
  const intraEdges = visibleEdges.filter((e) => !e.cross_subject)

  const allCrossEdgesMap = useMemo(() => {
    const map = new Map()
    edges.forEach((e) => {
      if (!e.cross_subject) return
      if (!map.has(e.source)) map.set(e.source, [])
      if (!map.has(e.target)) map.set(e.target, [])
      map.get(e.source).push({ type: 'outbound', to: e.target })
      map.get(e.target).push({ type: 'inbound', from: e.source })
    })
    return map
  }, [edges])

  // Mouse drag pointer calculation handlers
  const handlePointerDown = (e) => {
    if (e.target.tagName === 'rect' || e.target.tagName === 'text' || e.target.tagName === 'circle') return
    setIsDragging(true)
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
  }

  const handlePointerMove = (e) => {
    if (!isDragging) return
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y })
  }

  const handlePointerUp = () => setIsDragging(false)

  const handleWheel = (e) => {
    e.preventDefault()
    const zoomFactor = 1.1
    const nextZoom = e.deltaY < 0 ? Math.min(zoom * zoomFactor, 2) : Math.max(zoom / zoomFactor, 0.3)

    const rect = containerRef.current.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    setPan((prev) => ({
      x: mouseX - (mouseX - prev.x) * (nextZoom / zoom),
      y: mouseY - (mouseY - prev.y) * (nextZoom / zoom),
    }))
    setZoom(nextZoom)
  }

  const zoomBy = (factor) => {
    setZoom((z) => Math.max(0.3, Math.min(2.0, z * factor)))
  }

  const resetView = () => {
    setZoom(0.8)
    if (containerRef.current) {
      setPan({
        x: (containerRef.current.clientWidth - totalWidth * 0.8) / 2,
        y: (containerRef.current.clientHeight - maxHeight * 0.8) / 2
      })
    }
  }

  const spinOffset = (spinTick * 2) % 360

  return (
      <div
          ref={containerRef}
          style={{
            position: 'relative',
            width: '100%',
            height: '100%',
            background: '#0d0d14',
            overflow: 'hidden',
            touchAction: 'none'
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          onWheel={handleWheel}
      >
        <svg
            width="100%"
            height="100%"
            style={{ display: 'block', cursor: isDragging ? 'grabbing' : 'grab' }}
            onClick={() => onSelectNode(null)}
        >
          {/* Transform Matrix Viewport wrap */}
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>

            {/* ── SUBJECT CONTAINER ENCLOSURES ── */}
            {subjects.map((sub) => {
              const subNodes = layoutNodes.filter((n) => (n.subject || n.name) === sub)
              if (!subNodes.length) return null

              const positions = subNodes.map((n) => pos[n.id]).filter(Boolean)
              if (!positions.length) return null

              const minX = Math.min(...positions.map((p) => p.x)) - 24
              const maxX = Math.max(...positions.map((p) => p.x + p.w)) + 24
              const minY = Math.min(...positions.map((p) => p.y)) - 20
              const maxY = Math.max(...positions.map((p) => p.y + p.h)) + 24

              return (
                  <g key={`subj-container-${sub}`} opacity={focus ? 0.35 : 1} style={{ transition: 'opacity 0.2s' }}>
                    <rect
                        x={minX} y={minY} width={maxX - minX} height={maxY - minY}
                        fill="rgba(30, 41, 59, 0.12)"
                        stroke="rgba(51, 65, 85, 0.4)"
                        strokeWidth={1.5}
                        rx={12}
                    />
                    <text
                        x={minX + 16} y={minY + 24}
                        fill="rgba(148, 163, 184, 0.45)"
                        fontSize={12}
                        fontFamily="var(--font-mono)"
                        letterSpacing="0.08em"
                        fontWeight="600"
                    >
                      {sub.toUpperCase()}
                    </text>
                  </g>
              )
            })}

            {/* ── Tree Edges ── */}
            {treeEdges.map(({ parentId, childId }) => {
              const p = pos[parentId]
              const c = pos[childId]
              if (!p || !c) return null
              const px   = p.x + p.w / 2
              const py   = p.y + p.h
              const cx   = c.x + c.w / 2
              const cy   = c.y
              const midY = (py + cy) / 2
              const lit  = isTreeEdgeLit(parentId, childId)
              return (
                  <path
                      key={`t-${parentId}-${childId}`}
                      d={`M${px},${py} C${px},${midY} ${cx},${midY} ${cx},${cy}`}
                      fill="none"
                      stroke={p.color?.edge || '#534AB7'}
                      strokeWidth={1}
                      strokeOpacity={lit ? 0.4 : 0.04}
                  />
              )
            })}

            {/* ── Cross-Subject Bridges ── */}
            {crossEdges.map((e, i) => {
              const p1 = pos[e.source]
              const p2 = pos[e.target]
              if (!p1 || !p2) return null
              const x1  = p1.x + p1.w / 2
              const y1  = p1.y + p1.h / 2
              const x2  = p2.x + p2.w / 2
              const y2  = p2.y + p2.h / 2
              const mx  = (x1 + x2) / 2
              const my  = (y1 + y2) / 2

              return (
                  <path
                      key={`cx-${i}`}
                      d={`M${x1},${y1} Q${mx},${my + 60} ${x2},${y2}`}
                      fill="none"
                      stroke="#a78bfa"
                      strokeWidth={1.5}
                      strokeDasharray="4 3"
                      strokeOpacity={1}
                  />
              )
            })}

            {/* ── Intra-Subject Connections: Hidden by default (0 opacity), routes via side-gutters ── */}
            {intraEdges.map((e, i) => {
              const p1 = pos[e.source]
              const p2 = pos[e.target]
              if (!p1 || !p2) return null

              const x1 = p1.x + p1.w / 2
              const y1 = p1.y + p1.h / 2
              const x2 = p2.x + p2.w / 2
              const y2 = p2.y + p2.h / 2

              const lit = isSemanticEdgeLit(e)
              const color = SEMANTIC_COLORS[e.rel_type] || SEMANTIC_COLORS.related

              const srcNode = nodeMap[e.source]
              const subNodes = layoutNodes.filter((n) => (n.subject || n.name) === srcNode.subject)
              const positions = subNodes.map((n) => pos[n.id]).filter(Boolean)

              const minX = positions.length ? Math.min(...positions.map((p) => p.x)) : p1.x
              const maxX = positions.length ? Math.max(...positions.map((p) => p.x + p.w)) : p1.x + p1.w

              const useLeftGutter = x1 <= minX + (maxX - minX) / 2
              const gutterX = useLeftGutter ? (minX - 16) : (maxX + 16)

              const startX = useLeftGutter ? p1.x : (p1.x + p1.w)
              const endX   = useLeftGutter ? p2.x : (p2.x + p2.w)

              const pathData = `M ${startX} ${y1} H ${gutterX} V ${y2} H ${endX}`

              return (
                  <g key={`intra-gutter-${i}`}>
                    <path
                        d={pathData}
                        fill="none"
                        stroke="transparent"
                        strokeWidth={8}
                        style={{ cursor: 'pointer' }}
                    />
                    <path
                        d={pathData}
                        fill="none"
                        stroke={color}
                        strokeWidth={lit ? 1.5 : 1}
                        strokeOpacity={lit ? 0.8 : 0} // Set to 0 to completely clean canvas unless selected
                        style={{ transition: 'stroke-opacity 0.2s', pointerEvents: 'none' }}
                    />
                  </g>
              )
            })}

            {/* ── Nodes Layer ── */}
            {layoutNodes.map((n) => {
              const p = pos[n.id]
              if (!p) return null
              const colorSet   = p.color
              const tier       = p.tier ?? 2
              const isSelected = n.id === selectedNode
              const isHovered  = n.id === hoveredNode
              const lit        = isNodeHighlighted(n.id)
              const isSubject  = tier === 0

              const hasTopic     = topicsWithSubtopics.has(n.id)
              const topicCollapsed = collapsedTopics.has(n.id)

              const hasSubjectContent = isSubject && subjectsWithTopics.has(n.subject || n.name)
              const subjCollapsed     = collapsedSubjects.has(n.id)

              let fillColor, textColor, strokeColor
              if (tier === 0)      { fillColor = colorSet.root; textColor = colorSet.text_root; strokeColor = colorSet.root  }
              else if (tier === 1) { fillColor = colorSet.cat;  textColor = colorSet.text_root; strokeColor = colorSet.cat   }
              else                 { fillColor = colorSet.leaf; textColor = colorSet.text_leaf; strokeColor = colorSet.cat   }

              const rx         = tier === 0 ? 10 : tier === 1 ? 8 : 6
              const fontSize   = tier === 0 ? 13 : tier === 1 ? 12 : 11
              const fontWeight = tier <= 1 ? '500' : '400'
              const sw         = tier === 0 ? 1 : 0.5
              const hw = p.w / 2
              const hh = p.h / 2

              const { display: labelText, truncated } = truncateLabel(n.name, fontSize)

              const relationshipPortals = allCrossEdgesMap.get(n.id) || []
              const hasOutboundPortal = relationshipPortals.some(r => r.type === 'outbound')
              const hasInboundPortal = relationshipPortals.some(r => r.type === 'inbound')

              return (
                  <g
                      key={n.id}
                      transform={`translate(${p.x + hw},${p.y + hh})`}
                      style={{
                        cursor: 'pointer',
                        filter: (isHovered || isSelected) ? `drop-shadow(0 0 7px ${colorSet.edge})` : undefined,
                        transition: 'opacity 0.2s',
                      }}
                      opacity={lit ? 1 : 0.08}
                      onClick={(e) => { e.stopPropagation(); onSelectNode(n.id === selectedNode ? null : n.id) }}
                      onMouseEnter={() => onHoverNode(n.id)}
                      onMouseLeave={() => onHoverNode(null)}
                  >
                    {truncated && <title>{n.name}</title>}

                    {isSelected && (
                        <rect
                            x={-hw - 4} y={-hh - 4} width={p.w + 8} height={p.h + 8}
                            rx={rx + 3} fill="none"
                            stroke={colorSet.edge} strokeWidth={1.5}
                            strokeDasharray="6 3" strokeDashoffset={spinOffset}
                            opacity={0.9}
                        />
                    )}

                    {isHovered && !isSelected && (
                        <rect
                            x={-hw - 3} y={-hh - 3} width={p.w + 6} height={p.h + 6}
                            rx={rx + 2} fill="none"
                            stroke={colorSet.edge} strokeWidth={1} opacity={0.3}
                        />
                    )}

                    <rect
                        x={-hw} y={-hh} width={p.w} height={p.h}
                        rx={rx}
                        fill={fillColor}
                        stroke={strokeColor}
                        strokeWidth={isSelected ? 1 : sw}
                        strokeOpacity={0.65}
                    />

                    <text
                        textAnchor="middle" dominantBaseline="central"
                        fontSize={fontSize}
                        fontFamily="var(--font-mono)"
                        fontWeight={fontWeight}
                        fill={isSelected ? '#ffffff' : textColor}
                        style={{ pointerEvents: 'none', userSelect: 'none' }}
                    >
                      {labelText}
                    </text>

                    {/* Local Link Badges to clean visual paths */}
                    {!isSubject && !focus && hasOutboundPortal && (
                        <g transform={`translate(${hw - 8}, ${hh - 8})`}>
                          <circle r={5.5} fill="#1e1b4b" stroke="#a78bfa" strokeWidth={0.5} />
                          <text textAnchor="middle" dominantBaseline="central" fontSize={7} fill="#c084fc" fontWeight="bold">↗</text>
                        </g>
                    )}
                    {!isSubject && !focus && hasInboundPortal && !hasOutboundPortal && (
                        <g transform={`translate(${hw - 8}, ${hh - 8})`}>
                          <circle r={5.5} fill="#1e1b4b" stroke="#64748b" strokeWidth={0.5} />
                          <text textAnchor="middle" dominantBaseline="central" fontSize={7} fill="#94a3b8" fontWeight="bold">↘</text>
                        </g>
                    )}

                    {hasSubjectContent && (
                        <g
                            transform={`translate(${hw - 9},${-hh + 9})`}
                            style={{ cursor: 'pointer' }}
                            onClick={(e) => { e.stopPropagation(); toggleSubject(n.id) }}
                        >
                          <circle r={7} fill={colorSet.cat} opacity={0.95} />
                          <text
                              textAnchor="middle" dominantBaseline="central"
                              fontSize={9} fill={colorSet.text_root} fontWeight="bold"
                          >
                            {subjCollapsed ? '▶' : '▼'}
                          </text>
                        </g>
                    )}

                    {hasTopic && !isSubject && (
                        <g
                            transform={`translate(${hw - 9},${-hh + 9})`}
                            style={{ cursor: 'pointer' }}
                            onClick={(e) => { e.stopPropagation(); onToggleTopic(n.id) }}
                        >
                          <circle r={7} fill={colorSet.cat} opacity={0.95} />
                          <text
                              textAnchor="middle" dominantBaseline="central"
                              fontSize={10} fill={colorSet.text_root} fontWeight="bold"
                          >
                            {topicCollapsed ? '+' : '−'}
                          </text>
                        </g>
                    )}
                  </g>
              )
            })}
          </g>
        </svg>

        {/* Static Fixed Legend */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          display: 'flex', gap: 20, padding: '10px 20px',
          fontSize: 11, color: '#64748b',
          fontFamily: 'var(--font-mono)',
          background: 'linear-gradient(transparent, #0d0d14 60%)',
          pointerEvents: 'none',
          zIndex: 10
        }}>
          {[
            { label: 'Subject',  fillOpacity: 1    },
            { label: 'Topic',    fillOpacity: 0.88 },
            { label: 'Subtopic', fillOpacity: 0.18 },
          ].map(({ label, fillOpacity }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <svg width={10} height={10} style={{ flexShrink: 0 }}>
                  <rect width={10} height={10} rx={2}
                        fill="#534AB7" fillOpacity={fillOpacity}
                        stroke="#534AB7" strokeWidth={0.5} strokeOpacity={0.65} />
                </svg>
                {label}
              </div>
          ))}
        </div>

        {/* Static UI Zoom Matrix HUD */}
        <div style={{
          position: 'absolute', bottom: 36, right: 16,
          display: 'flex', flexDirection: 'column', gap: 6, zIndex: 10,
        }}>
          <button style={BTN} onClick={() => zoomBy(1.2)}>+</button>
          <button style={BTN} onClick={() => zoomBy(0.8)}>−</button>
          <button style={{ ...BTN, fontSize: 11 }} onClick={resetView}>⊡</button>
        </div>
      </div>
  )
}
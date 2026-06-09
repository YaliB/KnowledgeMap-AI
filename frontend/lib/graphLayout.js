export const DOMAIN_COLORS = {
  default_palette: [
    { root: '#534AB7', cat: '#3C3489', leaf: '#534AB733', text_root: '#EEEDFE', text_leaf: '#AFA9EC', edge: '#534AB7' },
    { root: '#0F6E56', cat: '#085041', leaf: '#0F6E5633', text_root: '#E1F5EE', text_leaf: '#5DCAA5', edge: '#0F6E56' },
    { root: '#185FA5', cat: '#0C447C', leaf: '#185FA533', text_root: '#E6F1FB', text_leaf: '#85B7EB', edge: '#185FA5' },
    { root: '#993C1D', cat: '#712B13', leaf: '#993C1D33', text_root: '#FAECE7', text_leaf: '#F0997B', edge: '#993C1D' },
    { root: '#993556', cat: '#72243E', leaf: '#99355633', text_root: '#FBEAF0', text_leaf: '#ED93B1', edge: '#993556' },
  ],
}

export function getDomainColor(index) {
  const p = DOMAIN_COLORS.default_palette
  return p[((index % p.length) + p.length) % p.length]
}

export const subjectToColor = (subject, subjects) =>
    getDomainColor(subjects.indexOf(subject)).root

// Column layout constants (Adjusted for comfortable 2-column distribution)
export const COL = {
  WIDTH:              340,   // Widened from 220 to naturally fit 2 subtopic blocks
  GAP:                70,    // Space between subject containers
  PADDING_TOP:        60,
  PADDING_LEFT:       40,
  PADDING_BOTTOM:     60,
  SUBJECT_H:          44,
  TOPIC_H:            36,
  SUBTOPIC_H:         30,
  TOPIC_GAP:          12,
  SUBTOPIC_GAP:       10,    // Space between rows
  SUBTOPIC_X_GAP:     12,    // Space between left/right subtopic columns
  SUBJECT_TO_TOPIC:   40,
  TOPIC_TO_SUBTOPIC:  40,
  NODE_WIDTH:         155,   // Individual width of a subtopic box to fit 2-up inside COL.WIDTH
  CROSS_EDGE_Y:       20,
}

// Main layout entry point.
// Each subject gets one container column; subtopics spread into pairs horizontally.
export function computeLayout(subjects, nodes) {
  const colorMap = {}
  subjects.forEach((s, i) => { colorMap[s] = getDomainColor(i).root })

  if (!nodes.length) return { pos: {}, colorMap, totalWidth: 0, maxHeight: 0 }

  const nameToNode = new Map(nodes.map((n) => [n.name, n]))

  // Group nodes by level
  const subjectNodes  = nodes.filter((n) => n.level === 'subject')
  const topicsBySubj  = new Map()
  const subtopicsByTopic = new Map()

  nodes.forEach((n) => {
    if (n.level === 'topic') {
      const arr = topicsBySubj.get(n.subject) || []
      arr.push(n)
      topicsBySubj.set(n.subject, arr)
    }
    if (n.level === 'subtopic') {
      const parent = nameToNode.get(n.parent)
      if (parent) {
        const arr = subtopicsByTopic.get(parent.id) || []
        arr.push(n)
        subtopicsByTopic.set(parent.id, arr)
      }
    }
  })

  // Column order follows the global subjects array
  const visibleSubjectNames = subjects.filter((s) =>
      subjectNodes.some((n) => n.subject === s || n.name === s)
  )

  const pos = {}
  let maxHeight = COL.PADDING_TOP + COL.SUBJECT_H + COL.PADDING_BOTTOM

  visibleSubjectNames.forEach((subjectName, colIdx) => {
    const subjNode = subjectNodes.find((n) => n.subject === subjectName || n.name === subjectName)
    if (!subjNode) return

    const colorIndex = subjects.indexOf(subjectName)
    const colorSet   = getDomainColor(colorIndex >= 0 ? colorIndex : colIdx)
    const colX       = COL.PADDING_LEFT + colIdx * (COL.WIDTH + COL.GAP)

    // Calculate centering offset for the wider Topic/Subject headings
    const headerWidth = COL.WIDTH - 20
    const headerX     = colX + 10

    // Subject node (Centered at top of column)
    pos[subjNode.id] = {
      x: headerX, y: COL.PADDING_TOP,
      w: headerWidth, h: COL.SUBJECT_H,
      tier: 0, color: colorSet,
    }

    let columnBottom = COL.PADDING_TOP + COL.SUBJECT_H
    const topics = topicsBySubj.get(subjectName) || []

    if (topics.length > 0) {
      // Position parent topics
      let topicY = columnBottom + COL.SUBJECT_TO_TOPIC
      topics.forEach((topic) => {
        pos[topic.id] = {
          x: headerX, y: topicY,
          w: headerWidth, h: COL.TOPIC_H,
          tier: 1, color: colorSet,
        }
        topicY += COL.TOPIC_H + COL.TOPIC_GAP
      })
      columnBottom = topicY - COL.TOPIC_GAP

      // Process subtopics sequentially by topic into a two-column grid layout
      let subtopicY = columnBottom + COL.TOPIC_TO_SUBTOPIC
      let anySubtopics = false

      topics.forEach((topic) => {
        const subtopics = subtopicsByTopic.get(topic.id) || []

        subtopics.forEach((subtopic, index) => {
          anySubtopics = true

          // Split across two columns: index % 2 determines left (0) or right (1)
          const isRightCol = index % 2 === 1
          const nodeX = isRightCol
              ? colX + 10 + COL.NODE_WIDTH + COL.SUBTOPIC_X_GAP
              : colX + 10

          pos[subtopic.id] = {
            x: nodeX,
            y: subtopicY,
            w: COL.NODE_WIDTH,
            h: COL.SUBTOPIC_H,
            tier: 2,
            color: colorSet,
          }

          // Advance y-coordinate down only after every second element (filling rows)
          if (isRightCol || index === subtopics.length - 1) {
            subtopicY += COL.SUBTOPIC_H + COL.SUBTOPIC_GAP
          }
        })
      })

      if (anySubtopics) columnBottom = subtopicY - COL.SUBTOPIC_GAP
    }

    maxHeight = Math.max(maxHeight, columnBottom + COL.PADDING_BOTTOM)
  })

  // Fallback for orphan nodes
  let orphanX = COL.PADDING_LEFT + visibleSubjectNames.length * (COL.WIDTH + COL.GAP)
  nodes.forEach((n) => {
    if (pos[n.id]) return
    pos[n.id] = {
      x: orphanX, y: COL.PADDING_TOP,
      w: COL.NODE_WIDTH, h: COL.SUBTOPIC_H,
      tier: 2, color: getDomainColor(0),
    }
    orphanX += COL.NODE_WIDTH + 20
  })

  const nCols = visibleSubjectNames.length
  const totalWidth = nCols > 0
      ? COL.PADDING_LEFT * 2 + nCols * COL.WIDTH + (nCols - 1) * COL.GAP
      : COL.PADDING_LEFT * 2

  return { pos, colorMap, totalWidth, maxHeight }
}

export function computeTreeLayout(rootId, nodes, edges, colorSet, offsetX = 0) {
  return []
}
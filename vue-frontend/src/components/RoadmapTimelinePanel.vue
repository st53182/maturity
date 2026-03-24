<template>
  <div class="rm-timeline">
    <p v-if="hint" class="rm-timeline__hint">{{ hint }}</p>
    <div v-if="!laneBlocks.length" class="rm-timeline__empty">Нет элементов для отображения.</div>
    <div v-else class="rm-timeline__scroll">
      <div class="rm-timeline__grid">
        <div class="rm-timeline__corner" aria-hidden="true" />
        <div class="rm-timeline__header">
          <div
            v-for="(q, qi) in quarterColumns"
            :key="qi"
            class="rm-timeline__qcol"
            :style="{ width: q.widthPct + '%' }"
          >
            <span class="rm-timeline__qlabel">{{ q.label }}</span>
            <div class="rm-timeline__qgrid" />
          </div>
        </div>

        <template v-for="(block, bi) in laneBlocks" :key="'b-' + bi">
          <div class="rm-timeline__stream" :style="{ gridColumn: '1 / -1' }">
            <span class="rm-timeline__stream-label" :style="{ borderLeftColor: block.color }">{{ block.streamLabel }}</span>
          </div>
          <template v-for="row in block.rows" :key="row.key">
            <div class="rm-timeline__row-label" :title="row.label">{{ row.label }}</div>
            <div class="rm-timeline__row-track">
              <div
                v-for="(g, gi) in quarterColumns"
                :key="'g-' + gi"
                class="rm-timeline__cell"
                :style="{ width: g.widthPct + '%' }"
              />
              <button
                v-for="bar in row.bars"
                :key="bar.id"
                type="button"
                class="rm-timeline__bar"
                :class="bar.type === 'epic' ? 'rm-timeline__bar--epic' : 'rm-timeline__bar--story'"
                :style="{
                  ...barStyle(bar),
                  backgroundColor: bar.tint,
                  borderColor: bar.stroke
                }"
                :title="bar.title + (bar.inferred ? ' (дата по позиции на доске)' : '')"
                @click="$emit('select-item', bar.id)"
              >
                <span class="rm-timeline__bar-text">{{ bar.title }}</span>
              </button>
            </div>
          </template>
        </template>
      </div>

      <svg
        v-if="dependencyPaths.length"
        class="rm-timeline__deps"
        :viewBox="`0 0 100 ${Math.max(1, timelineRowCount)}`"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          v-for="(p, pi) in dependencyPaths"
          :key="'p-' + pi"
          :d="p.d"
          fill="none"
          :stroke="p.stroke"
          stroke-width="0.12"
          vector-effect="non-scaling-stroke"
          stroke-dasharray="0.35 0.25"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
  </div>
</template>

<script>
/**
 * Таймлайн для боевой дорожной карты: swimlanes по metadata.stream (или по командам),
 * даты в metadata.start / metadata.end; при отсутствии дат — оценка по position_x и сетке кварталов mxGraph.
 */
const QUARTER_WIDTH = 800
const QUARTER_GAP = 50
const CANVAS_START_X = 50

const STREAM_PALETTE = [
  { fill: '#e8eeff', stroke: '#2754c7' },
  { fill: '#fce7f3', stroke: '#be185d' },
  { fill: '#d1fae5', stroke: '#047857' },
  { fill: '#fef3c7', stroke: '#b45309' },
  { fill: '#e0f2fe', stroke: '#0369a1' },
  { fill: '#ede9fe', stroke: '#6d28d9' }
]

function iso(d) {
  const x = d instanceof Date ? d : new Date(d)
  return x.toISOString().slice(0, 10)
}

function parseQuarter(qs) {
  const m = String(qs || '').match(/(\d{4})-Q([1-4])/i)
  if (!m) return null
  return { year: parseInt(m[1], 10), q: parseInt(m[2], 10) }
}

function defaultPeriod(quarterStart) {
  const p = parseQuarter(quarterStart)
  if (!p) {
    const t = new Date()
    const start = new Date(t.getFullYear(), t.getMonth(), 1)
    const end = new Date(start)
    end.setMonth(end.getMonth() + 6)
    end.setDate(end.getDate() - 1)
    return { start: iso(start), end: iso(end) }
  }
  const start = new Date(p.year, (p.q - 1) * 3, 1)
  const end = new Date(start)
  end.setMonth(end.getMonth() + 12)
  end.setDate(end.getDate() - 1)
  return { start: iso(start), end: iso(end) }
}

function mergePeriodWithDates(period, items, resolveBar) {
  let minT = new Date(period.start + 'T12:00:00').getTime()
  let maxT = new Date(period.end + 'T12:00:00').getTime()
  for (const item of items) {
    const b = resolveBar(item)
    if (b.start) minT = Math.min(minT, new Date(b.start + 'T12:00:00').getTime())
    if (b.end) maxT = Math.max(maxT, new Date(b.end + 'T12:00:00').getTime())
  }
  if (maxT <= minT) maxT = minT + 30 * 86400000
  return { start: iso(new Date(minT)), end: iso(new Date(maxT)) }
}

function inferDatesFromPosition(item, quarterStart) {
  const period = defaultPeriod(quarterStart)
  const ps = new Date(period.start + 'T12:00:00').getTime()
  const pe = new Date(period.end + 'T12:00:00').getTime()
  const span = Math.max(1, pe - ps)
  const totalW = 4 * (QUARTER_WIDTH + QUARTER_GAP)
  const x = (item.position_x ?? 100) - CANVAS_START_X
  const frac = Math.max(0, Math.min(1, x / totalW))
  const barMs = Math.min(span * 0.15, 21 * 86400000)
  const s = ps + frac * Math.max(0, span - barMs)
  const e = s + Math.max(barMs, 7 * 86400000)
  return { start: iso(new Date(s)), end: iso(new Date(e)), inferred: true }
}

function quartersForPeriod(period) {
  const endMs = new Date(period.end + 'T12:00:00').getTime()
  const out = []
  let cur = new Date(period.start + 'T12:00:00')
  cur.setDate(1)
  const m0 = cur.getMonth()
  cur.setMonth(Math.floor(m0 / 3) * 3)
  let guard = 0
  while (cur.getTime() <= endMs && guard++ < 24) {
    const y = cur.getFullYear()
    const q = Math.floor(cur.getMonth() / 3) + 1
    const qStart = new Date(y, (q - 1) * 3, 1)
    const qEnd = new Date(y, q * 3, 0)
    out.push({ label: `Q${q} ${y}`, qStart, qEnd })
    cur = new Date(y, q * 3, 1)
  }
  if (!out.length) {
    out.push({ label: 'Период', qStart: new Date(period.start), qEnd: new Date(period.end) })
  }
  return out
}

function barPct(startIso, endIso, period) {
  const ps = new Date(period.start + 'T12:00:00').getTime()
  const pe = new Date(period.end + 'T12:00:00').getTime()
  const span = Math.max(1, pe - ps)
  const s = new Date(startIso + 'T12:00:00').getTime()
  const e = new Date(endIso + 'T12:00:00').getTime()
  const left = ((s - ps) / span) * 100
  const width = ((e - s) / span) * 100
  return {
    left: `${Math.max(0, Math.min(99.5, left))}%`,
    width: `${Math.max(0.35, Math.min(100 - left, width))}%`
  }
}

export default {
  name: 'RoadmapTimelinePanel',
  props: {
    items: { type: Array, default: () => [] },
    dependencies: { type: Array, default: () => [] },
    teams: { type: Array, default: () => [] },
    quarterStart: { type: String, default: '' },
    readOnly: { type: Boolean, default: false }
  },
  emits: ['select-item'],
  computed: {
    hint() {
      if (this.readOnly) return ''
      return 'Направление и даты таймлайна задаются в карточке элемента (поля ниже типа «Направление», «Начало», «Конец»). Без дат положение бара оценивается по горизонтали карточки на доске.'
    },
    teamNameById() {
      const m = new Map()
      for (const t of this.teams) m.set(t.id, t.name)
      return m
    },
    period() {
      const base = defaultPeriod(this.quarterStart)
      return mergePeriodWithDates(base, this.items, (it) => this.resolveBarDates(it))
    },
    quarterColumns() {
      const qs = quartersForPeriod(this.period)
      const w = 100 / qs.length
      return qs.map((q) => ({ ...q, widthPct: w }))
    },
    laneBlocks() {
      const items = this.items
      if (!items.length) return []
      const hasStream = items.some((it) => (it.metadata || {}).stream)
      const streamMap = new Map()

      const streamKey = (it) => {
        if (hasStream) return (it.metadata || {}).stream || 'Без направления'
        return '__all__'
      }
      const rowKey = (it) => {
        if (it.team_id != null) return `t-${it.team_id}`
        return 't-none'
      }
      const rowLabel = (it) => {
        if (it.team_id != null) return this.teamNameById.get(it.team_id) || `Команда ${it.team_id}`
        return 'Без команды'
      }

      for (const it of items) {
        const sk = streamKey(it)
        const rk = rowKey(it)
        if (!streamMap.has(sk)) streamMap.set(sk, new Map())
        const rows = streamMap.get(sk)
        if (!rows.has(rk)) rows.set(rk, { key: rk, label: rowLabel(it), items: [] })
        rows.get(rk).items.push(it)
      }

      const streamOrder = [...streamMap.keys()].sort((a, b) => {
        if (a === '__all__') return -1
        if (b === '__all__') return 1
        return a.localeCompare(b, 'ru')
      })

      let colorIdx = 0
      const blocks = []
      for (const sk of streamOrder) {
        const rows = streamMap.get(sk)
        const streamLabel = sk === '__all__' ? 'По командам' : sk
        const pal = STREAM_PALETTE[colorIdx % STREAM_PALETTE.length]
        colorIdx++
        const rowList = [...rows.values()].sort((a, b) => a.label.localeCompare(b.label, 'ru'))
        blocks.push({
          streamKey: sk,
          streamLabel,
          color: pal.stroke,
          rows: rowList.map((r) => ({
            key: r.key,
            label: r.label,
            bars: r.items.map((item) => {
              const dates = this.resolveBarDates(item)
              return {
                id: item.id,
                title: item.title,
                type: item.type,
                start: dates.start,
                end: dates.end,
                inferred: dates.inferred,
                tint: pal.fill,
                stroke: pal.stroke
              }
            })
          }))
        })
      }
      return blocks
    },
    /** Строки треков под SVG (без строки заголовка кварталов). */
    timelineRowCount() {
      let n = 0
      for (const b of this.laneBlocks) {
        n += 1 + b.rows.length
      }
      return Math.max(1, n)
    },
    barPositionsById() {
      const period = this.period
      const pos = new Map()
      let rowIdx = 0
      for (const block of this.laneBlocks) {
        rowIdx += 1
        for (const row of block.rows) {
          for (const bar of row.bars) {
            const ps = new Date(period.start + 'T12:00:00').getTime()
            const pe = new Date(period.end + 'T12:00:00').getTime()
            const span = Math.max(1, pe - ps)
            const s = new Date(bar.start + 'T12:00:00').getTime()
            const e = new Date(bar.end + 'T12:00:00').getTime()
            const left = ((s - ps) / span) * 100
            const right = ((e - ps) / span) * 100
            pos.set(bar.id, { row: rowIdx, left, right: Math.max(right, left + 0.5) })
          }
          rowIdx += 1
        }
      }
      return pos
    },
    dependencyPaths() {
      const pos = this.barPositionsById
      const paths = []
      for (const d of this.dependencies) {
        const a = pos.get(d.from_item_id)
        const b = pos.get(d.to_item_id)
        if (!a || !b) continue
        const y1 = a.row + 0.5
        const y2 = b.row + 0.5
        const x1 = a.right
        const x2 = b.left
        const midY = (y1 + y2) / 2
        const dStr = `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`
        const stroke = d.dependency_type === 'blocks' ? '#dc2626' : '#64748b'
        paths.push({ d: dStr, stroke })
      }
      return paths
    }
  },
  methods: {
    resolveBarDates(item) {
      const md = item.metadata || {}
      let start = md.start || md.timeline_start
      let end = md.end || md.timeline_end
      let inferred = false
      if (start && !end) {
        const t = new Date(start + 'T12:00:00')
        t.setDate(t.getDate() + 14)
        end = iso(t)
      }
      if (end && !start) {
        const t = new Date(end + 'T12:00:00')
        t.setDate(t.getDate() - 14)
        start = iso(t)
      }
      if (!start || !end) {
        const inf = inferDatesFromPosition(item, this.quarterStart)
        start = start || inf.start
        end = end || inf.end
        inferred = !md.start && !md.end && !md.timeline_start && !md.timeline_end
      }
      return { start, end, inferred }
    },
    barStyle(bar) {
      return barPct(bar.start, bar.end, this.period)
    }
  }
}
</script>

<style scoped>
.rm-timeline {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  font-size: 0.8125rem;
  color: var(--vl-text, #0d1733);
}

.rm-timeline__hint {
  margin: 0 0 0.65rem;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  background: rgba(39, 84, 199, 0.08);
  color: var(--vl-muted, #5d6b8a);
  font-size: 0.75rem;
  line-height: 1.45;
}

.rm-timeline__empty {
  padding: 2rem;
  text-align: center;
  color: var(--vl-muted, #5d6b8a);
}

.rm-timeline__scroll {
  position: relative;
  flex: 1;
  min-height: 280px;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background: #fff;
}

.rm-timeline__grid {
  display: grid;
  grid-template-columns: 13rem 1fr;
  min-width: 640px;
}

.rm-timeline__corner {
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
  border-right: 1px solid var(--vl-border, #d8e0f0);
  background: var(--vl-surface-soft, #f6f9ff);
}

.rm-timeline__header {
  display: flex;
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
  background: var(--vl-surface-soft, #f6f9ff);
}

.rm-timeline__qcol {
  flex-shrink: 0;
  box-sizing: border-box;
  padding: 0.4rem 0.35rem;
  border-right: 1px solid var(--vl-border, #d8e0f0);
  text-align: center;
}

.rm-timeline__qlabel {
  display: block;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--vl-muted, #5d6b8a);
}

.rm-timeline__qgrid {
  margin-top: 0.25rem;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(39, 84, 199, 0.12), rgba(39, 84, 199, 0.04));
}

.rm-timeline__stream {
  display: flex;
  align-items: center;
  min-height: 2.75rem;
  padding: 0.35rem 0.75rem;
  background: rgba(10, 20, 45, 0.04);
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
}

.rm-timeline__stream-label {
  font-size: 0.6875rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-left: 4px solid var(--vl-primary-end, #2754c7);
  padding-left: 0.5rem;
}

.rm-timeline__row-label {
  padding: 0.5rem 0.65rem;
  border-right: 1px solid var(--vl-border, #d8e0f0);
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
  background: #fbfcff;
  font-weight: 600;
  font-size: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  align-self: stretch;
  display: flex;
  align-items: center;
  min-height: 2.75rem;
}

.rm-timeline__row-track {
  position: relative;
  border-bottom: 1px solid var(--vl-border, #d8e0f0);
  min-height: 2.75rem;
  display: flex;
  align-items: stretch;
}

.rm-timeline__cell {
  flex-shrink: 0;
  box-sizing: border-box;
  border-right: 1px solid rgba(216, 224, 240, 0.85);
  background: rgba(246, 249, 255, 0.35);
}

.rm-timeline__bar {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 1.5rem;
  max-width: calc(100% - 6px);
  border-radius: 8px;
  border-width: 1px;
  border-style: solid;
  padding: 0 0.4rem;
  cursor: pointer;
  text-align: left;
  box-shadow: 0 1px 3px rgba(10, 20, 45, 0.08);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.rm-timeline__bar:hover {
  box-shadow: 0 3px 10px rgba(10, 20, 45, 0.12);
  z-index: 2;
}

.rm-timeline__bar-text {
  display: block;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--vl-text, #0d1733);
}

.rm-timeline__bar--epic .rm-timeline__bar-text {
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.rm-timeline__deps {
  position: absolute;
  left: 13rem;
  right: 0;
  top: 2.5rem;
  bottom: 0;
  width: calc(100% - 13rem);
  height: calc(100% - 2.5rem);
  pointer-events: none;
  z-index: 1;
}
</style>

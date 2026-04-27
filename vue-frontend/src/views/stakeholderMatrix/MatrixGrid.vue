<template>
  <div class="sh-mx">
    <p v-if="highlightRids && highlightRids.length" class="sh-mx__event-hint">
      <span>🎯</span>
      <strong>{{ $t('agileTraining.stakeholderMatrix.screens.matrix.eventBadge') }}:</strong>
      <span class="sh-mx__event-list">
        <span v-for="rid in highlightRids" :key="rid" class="sh-mx__event-tag">
          {{ personaEmoji(rid) }} {{ personaName(rid) }}
        </span>
      </span>
    </p>
    <div
      class="sh-mx__pool"
      @dragover.prevent
      @drop.prevent="onDropPool($event)"
    >
      <div class="sh-mx__pool-h">{{ $t('agileTraining.stakeholderMatrix.matrix.pool') }}</div>
      <div class="sh-mx__chips">
        <div
          v-for="rid in unplacedIds"
          :key="rid"
          class="sh-chip"
          :class="{ 'sh-chip--hl': highlightSet.has(rid) }"
          draggable="true"
          @dragstart="onDragStart($event, rid)"
        >
          <span class="sh-chip__emoji">{{ personaEmoji(rid) }}</span>
          <span class="sh-chip__name">{{ personaName(rid) }}</span>
        </div>
      </div>
    </div>
    <div class="sh-mx__wrap">
      <div class="sh-mx__y-label">{{ axisY }}</div>
      <div class="sh-mx__grid-outer">
        <div
          v-for="infl in [2, 1, 0]"
          :key="'infl' + infl"
          class="sh-mx__row"
        >
          <div class="sh-mx__y-tick">{{ yTick(infl) }}</div>
          <div
            v-for="intv in [0, 1, 2]"
            :key="infl + '-' + intv"
            class="sh-mx__cell"
            :class="cellClass(infl, intv)"
            @dragover.prevent
            @drop.prevent="onDropCell($event, infl, intv)"
          >
            <div class="sh-mx__cell-tag">{{ cellTitle(infl, intv) }}</div>
            <div class="sh-mx__cell-items">
              <div
                v-for="rid in rolesInCell(infl, intv)"
                :key="rid + '-' + infl + '-' + intv"
                class="sh-chip sh-chip--in"
                :class="{ 'sh-chip--hl': highlightSet.has(rid) }"
                draggable="true"
                @dragstart="onDragStart($event, rid)"
                :title="personaTitle(rid)"
              >
                <span class="sh-chip__emoji">{{ personaEmoji(rid) }}</span>
                <span class="sh-chip__name">{{ personaName(rid) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="sh-mx__x-ticks sh-mx__x-ticks--padded">
          <span v-for="(lb, j) in levelLabelsX" :key="'x'+j" class="sh-mx__tick">{{ lb }}</span>
        </div>
        <div class="sh-mx__x-c sh-mx__x-c--padded">{{ axisX }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { cellBucket } from './logic.js';

export default {
  name: 'MatrixGrid',
  props: {
    roundKey: { type: String, default: 'r1' },
    locale: { type: String, default: 'ru' },
    placements: { type: Object, required: true },
    allRoleIds: { type: Array, default: () => [] },
    contentCopy: { type: Object, default: () => ({}) },
    levelLabelsX: { type: Array, default: () => [] },
    levelLabelsY: { type: Array, default: () => [] },
    roleLabel: { type: Function, required: true },
    personaMap: { type: Object, default: () => ({}) },
    highlightRids: { type: Array, default: () => [] },
  },
  computed: {
    axisX() { return (this.contentCopy.axis && this.contentCopy.axis.x) || ''; },
    axisY() { return (this.contentCopy.axis && this.contentCopy.axis.y) || ''; },
    unplacedIds() {
      return (this.allRoleIds || []).filter((rid) => !this.placements[rid]);
    },
    highlightSet() {
      return new Set(this.highlightRids || []);
    },
  },
  methods: {
    personaEmoji(rid) {
      const p = this.personaMap[rid];
      return p ? p.emoji : '👤';
    },
    personaName(rid) {
      const p = this.personaMap[rid];
      return p ? p.name : rid;
    },
    personaTitle(rid) {
      const p = this.personaMap[rid];
      if (!p) return rid;
      return `${p.name} · ${p.role}`;
    },
    yTick(infl) {
      return (this.levelLabelsY && this.levelLabelsY[infl]) != null
        ? this.levelLabelsY[infl]
        : infl;
    },
    cellClass(infl, int) {
      return `sh-mx__cell--${cellBucket(infl, int)}`;
    },
    cellTitle(infl, int) {
      const b = cellBucket(infl, int);
      return (this.contentCopy.cell_strategy && this.contentCopy.cell_strategy[b]) || b;
    },
    rolesInCell(infl, int) {
      return (this.allRoleIds || []).filter((rid) => {
        const p = this.placements[rid];
        if (!p) return false;
        return p.infl === infl && p.int === int;
      });
    },
    onDragStart(ev, rid) {
      ev.dataTransfer.setData('text/plain', rid);
      ev.dataTransfer.effectAllowed = 'move';
    },
    onDropCell(ev, infl, int) {
      const rid = ev.dataTransfer.getData('text/plain');
      if (!rid) return;
      this.assign(rid, infl, int);
    },
    onDropPool(ev) {
      const rid = ev.dataTransfer.getData('text/plain');
      if (!rid) return;
      const next = { ...this.placements };
      delete next[rid];
      this.$emit('update:placements', next);
    },
    assign(rid, infl, int) {
      if (!(this.allRoleIds || []).includes(rid)) return;
      const next = { ...this.placements, [rid]: { infl, int } };
      this.$emit('update:placements', next);
    },
  },
};
</script>

<style scoped>
.sh-mx { display: flex; flex-direction: column; gap: 12px; }
.sh-mx__event-hint { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; padding: 8px 10px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; margin: 0; font-size: 12.5px; color: #92400e; line-height: 1.4; }
.sh-mx__event-list { display: inline-flex; flex-wrap: wrap; gap: 4px; }
.sh-mx__event-tag { background: #fff; border-radius: 999px; padding: 2px 8px; border: 1px solid rgba(245, 158, 11, 0.4); }
.sh-mx__pool { border: 1px dashed rgba(15, 23, 42, 0.2); border-radius: 10px; padding: 8px; background: #f8fafc; min-height: 48px; }
.sh-mx__pool-h { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-bottom: 4px; }
.sh-mx__chips { display: flex; flex-wrap: wrap; gap: 6px; }
.sh-mx__wrap { display: grid; grid-template-columns: 24px 1fr; gap: 4px; align-items: start; }
.sh-mx__y-label { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 11px; font-weight: 700; color: #64748b; line-height: 1.2; }
.sh-mx__grid-outer { min-width: 0; }
.sh-mx__row { display: grid; grid-template-columns: 40px 1fr 1fr 1fr; gap: 2px; align-items: stretch; }
.sh-mx__y-tick { font-size: 9px; font-weight: 700; color: #475569; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 1.1; }
.sh-mx__cell {
  min-height: 110px; border: 1px solid #0f172a; padding: 4px; font-size: 11px;
  display: flex; flex-direction: column;
}
.sh-mx__cell--minimal { background: #fff; }
.sh-mx__cell--informed { background: #eef2ff; }
.sh-mx__cell--satisfied { background: #c7d2fe; color: #0f172a; }
.sh-mx__cell--close { background: #1e3a8a; color: #f8fafc; }
.sh-mx__cell-tag { font-size: 9px; font-weight: 700; margin-bottom: 4px; opacity: 0.95; line-height: 1.1; text-transform: uppercase; letter-spacing: .04em; }
.sh-mx__x-ticks { display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center; font-size: 10px; font-weight: 600; color: #64748b; margin-top: 2px; }
.sh-mx__x-ticks--padded { padding-left: 40px; }
.sh-mx__x-c { text-align: center; font-size: 11px; font-weight: 700; color: #475569; margin-top: 4px; }
.sh-mx__x-c--padded { padding-left: 40px; }
.sh-mx__cell-items { flex: 1; display: flex; flex-direction: column; gap: 3px; overflow: auto; }
.sh-chip {
  display: inline-flex; align-items: center; gap: 4px;
  background: #fff; color: #1f2937; font-size: 11.5px; font-weight: 600;
  padding: 3px 6px; border-radius: 8px; cursor: grab; user-select: none;
  border: 1px solid rgba(15,23,42,0.12); max-width: 100%;
}
.sh-chip__emoji { font-size: 13px; flex-shrink: 0; }
.sh-chip__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sh-chip--in { background: #fff; }
.sh-mx__cell--informed .sh-chip--in { background: #fff; }
.sh-mx__cell--satisfied .sh-chip--in { background: rgba(255,255,255,0.85); }
.sh-mx__cell--close .sh-chip--in { background: rgba(255,255,255,0.95); color: #1e3a8a; border-color: rgba(255,255,255,0.7); }
.sh-chip--hl { box-shadow: 0 0 0 2px #f59e0b; border-color: #f59e0b; }
</style>

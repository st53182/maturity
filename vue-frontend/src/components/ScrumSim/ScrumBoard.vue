<template>
  <div class="sb" :class="{ 'sb--compact': compact }">
    <div
      v-for="col in columns"
      :key="col.key"
      class="sb__col"
      :class="['sb__col--' + col.key, { 'sb__col--highlight': highlightColumn === col.key }]"
    >
      <div class="sb__col-head">
        <span class="sb__col-title">{{ col.label }}</span>
        <span class="sb__col-count">{{ tasksIn(col.key).length }}</span>
      </div>
      <div class="sb__col-body">
        <div
          v-for="t in tasksIn(col.key)"
          :key="t.key"
          class="sb__card"
          :class="[
            'sb__card--' + (t.state || 'ok'),
            { 'sb__card--selectable': selectable, 'sb__card--selected': selectedKeys.includes(t.key) },
            { 'sb__card--pulse': pulseKeys.includes(t.key) }
          ]"
          @click="selectable ? $emit('task-click', t) : null"
        >
          <div class="sb__card-head">
            <span class="sb__card-emoji">{{ stateEmoji(t) }}</span>
            <span class="sb__card-title">{{ t.title }}</span>
            <span class="sb__card-cmpl" :title="$t('agileTraining.scrumSim.complexityTitle')">{{ effectiveComplexity(t) }}</span>
          </div>
          <div class="sb__card-desc" v-if="!compact">{{ t.desc }}</div>
          <div class="sb__card-meta">
            <span v-if="t.core" class="sb__badge sb__badge--core">{{ $t('agileTraining.scrumSim.core') }}</span>
            <span v-else class="sb__badge sb__badge--opt">{{ $t('agileTraining.scrumSim.optional') }}</span>
            <span v-if="t.origin === 'stakeholder'" class="sb__badge sb__badge--new">{{ $t('agileTraining.scrumSim.fromStakeholder') }}</span>
            <span v-if="t.origin === 'split'" class="sb__badge sb__badge--split">{{ $t('agileTraining.scrumSim.split') }}</span>
          </div>
          <div v-if="showProgress(t)" class="sb__card-progress">
            <div class="sb__progress">
              <div class="sb__progress-bar" :style="{ width: progressPct(t) + '%' }"></div>
            </div>
            <span class="sb__progress-text">{{ t.progress || 0 }}/{{ effectiveComplexity(t) }}</span>
          </div>
          <div v-if="t.state === 'blocked' && t.state_reason" class="sb__card-reason">🔴 {{ t.state_reason }}</div>
          <div v-else-if="t.state === 'rework' && t.state_reason" class="sb__card-reason">⚠️ {{ t.state_reason }}</div>
          <div v-else-if="t.state === 'risk' && t.state_reason" class="sb__card-reason">⚠️ {{ t.state_reason }}</div>
          <div v-if="hasBlockingDeps(t)" class="sb__card-deps">
            <span class="sb__deps-label">{{ $t('agileTraining.scrumSim.waitingFor') }}:</span>
            <span v-for="d in missingDeps(t)" :key="d" class="sb__deps-item">{{ titleOf(d) }}</span>
          </div>
          <div v-if="allocatedPts(t) > 0" class="sb__card-alloc">
            ⚙️ {{ $t('agileTraining.scrumSim.todayCapacity') }}: +{{ allocatedPts(t) }}
          </div>
        </div>
        <div v-if="tasksIn(col.key).length === 0" class="sb__empty">—</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ScrumBoard",
  props: {
    tasks: { type: Array, default: () => [] },
    columns: {
      type: Array,
      default: () => [
        { key: "product",     label: "Product Backlog" },
        { key: "backlog",     label: "Sprint Backlog" },
        { key: "in_progress", label: "В работе" },
        { key: "review",      label: "На проверке" },
        { key: "done",        label: "Завершено" },
      ],
    },
    compact: { type: Boolean, default: false },
    selectable: { type: Boolean, default: false },
    selectedKeys: { type: Array, default: () => [] },
    pulseKeys: { type: Array, default: () => [] },
    highlightColumn: { type: String, default: "" },
    allocation: { type: Object, default: () => ({}) },
    hideEmpty: { type: Boolean, default: false },
    hiddenColumns: { type: Array, default: () => [] },
  },
  emits: ["task-click"],
  computed: {
    taskMap() {
      const m = {};
      for (const t of this.tasks || []) m[t.key] = t;
      return m;
    },
  },
  methods: {
    tasksIn(colKey) {
      const arr = (this.tasks || []).filter(t => (t.column || "backlog") === colKey);
      return arr;
    },
    stateEmoji(t) {
      if (t.column === "done") return "🟢";
      if (t.state === "blocked") return "🔴";
      if (t.state === "rework") return "⚠️";
      if (t.state === "risk") return "⚠️";
      if (t.column === "review") return "🔵";
      if (t.column === "in_progress") return "🟡";
      return "⚪";
    },
    effectiveComplexity(t) {
      return Number(t.complexity || 0) + Number(t.extra || 0);
    },
    showProgress(t) {
      return ["in_progress", "review", "done"].includes(t.column);
    },
    progressPct(t) {
      const need = Math.max(1, this.effectiveComplexity(t));
      const cur = Math.max(0, Math.min(need, Number(t.progress || 0)));
      return Math.round((cur / need) * 100);
    },
    hasBlockingDeps(t) {
      if (!t.deps || !t.deps.length) return false;
      if (t.column === "done" || t.column === "product") return false;
      return t.deps.some(d => {
        const dep = this.taskMap[d];
        return dep && dep.column !== "done";
      });
    },
    missingDeps(t) {
      return (t.deps || []).filter(d => {
        const dep = this.taskMap[d];
        return dep && dep.column !== "done";
      });
    },
    titleOf(key) {
      const t = this.taskMap[key];
      return t ? t.title : key;
    },
    allocatedPts(t) {
      return Number((this.allocation || {})[t.key] || 0);
    },
  },
};
</script>

<style scoped>
.sb {
  display: grid;
  grid-template-columns: repeat(5, minmax(160px, 1fr));
  gap: 10px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  overflow-x: auto;
}
.sb--compact { padding: 6px; gap: 6px; }
.sb__col {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.sb__col--highlight {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}
.sb__col--product   { background: #f1f5f9; }
.sb__col--backlog   { background: #fef3c7; }
.sb__col--in_progress { background: #dbeafe; }
.sb__col--review    { background: #ede9fe; }
.sb__col--done      { background: #dcfce7; }
.sb__col-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; border-bottom: 1px solid #e2e8f0;
  font-size: 12px; font-weight: 700; color: #334155; letter-spacing: 0.02em;
  text-transform: uppercase;
}
.sb__col-count {
  background: #fff; border: 1px solid #cbd5e1; border-radius: 999px;
  padding: 1px 8px; font-size: 11px;
}
.sb__col-body { padding: 6px; display: flex; flex-direction: column; gap: 6px; }
.sb__empty { font-size: 11px; color: #94a3b8; text-align: center; padding: 12px 0; }

.sb__card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 8px 10px; font-size: 13px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.sb__card--selectable { cursor: pointer; }
.sb__card--selectable:hover { border-color: #0ea5e9; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08); }
.sb__card--selected { border-color: #0ea5e9; box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.3); }
.sb__card--blocked { background: #fef2f2; border-color: #fca5a5; }
.sb__card--rework  { background: #fff7ed; border-color: #fdba74; }
.sb__card--risk    { background: #fffbeb; border-color: #fcd34d; }
.sb__card--done    { background: #f0fdf4; border-color: #86efac; }
.sb__card--pulse   { animation: sb-pulse 1.2s ease-out 2; }
@keyframes sb-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.6); }
  60%  { box-shadow: 0 0 0 12px rgba(14, 165, 233, 0); }
  100% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0); }
}

.sb__card-head { display: flex; align-items: center; gap: 6px; }
.sb__card-emoji { font-size: 14px; }
.sb__card-title { flex: 1; font-weight: 600; color: #0f172a; font-size: 13px; line-height: 1.25; }
.sb__card-cmpl {
  background: #e0f2fe; color: #0369a1; border-radius: 6px;
  padding: 1px 6px; font-size: 11px; font-weight: 700;
}
.sb__card-desc { color: #475569; font-size: 12px; margin-top: 4px; line-height: 1.35; }
.sb__card-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.sb__badge {
  font-size: 10px; padding: 1px 6px; border-radius: 999px; font-weight: 600;
  border: 1px solid transparent;
}
.sb__badge--core  { background: #dbeafe; color: #1e40af; }
.sb__badge--opt   { background: #f1f5f9; color: #475569; }
.sb__badge--new   { background: #fce7f3; color: #be185d; }
.sb__badge--split { background: #ecfccb; color: #4d7c0f; }

.sb__card-progress { margin-top: 6px; display: flex; align-items: center; gap: 6px; }
.sb__progress { flex: 1; height: 6px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.sb__progress-bar { height: 100%; background: linear-gradient(90deg, #0ea5e9, #6366f1); border-radius: 999px; transition: width 0.3s; }
.sb__progress-text { font-size: 11px; color: #475569; font-variant-numeric: tabular-nums; }

.sb__card-reason { font-size: 11px; color: #b91c1c; margin-top: 6px; line-height: 1.3; }
.sb__card--rework .sb__card-reason, .sb__card--risk .sb__card-reason { color: #b45309; }
.sb__card-deps { font-size: 11px; color: #64748b; margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.sb__deps-label { color: #94a3b8; }
.sb__deps-item { background: #f1f5f9; padding: 1px 6px; border-radius: 6px; }
.sb__card-alloc { font-size: 11px; color: #0369a1; margin-top: 6px; font-weight: 600; }

@media (max-width: 900px) {
  .sb { grid-template-columns: repeat(5, 180px); }
}
</style>

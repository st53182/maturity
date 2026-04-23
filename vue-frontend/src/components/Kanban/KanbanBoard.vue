<template>
  <div class="kanban-board">
    <!-- Toolbar: swimlane controls -->
    <div class="kanban-board__toolbar" v-if="editable" data-html2canvas-ignore="true">
      <button type="button" class="kbb-btn kbb-btn--ghost" @click="onAddSwimlane">+ {{ t.addSwimlane }}</button>
      <button type="button" class="kbb-btn kbb-btn--ghost" @click="$emit('seed-swimlanes')">📋 {{ t.seedSwimlanes }}</button>
    </div>

    <!-- Warnings -->
    <div class="kanban-board__warnings" v-if="!workflow.length">
      <div class="kbb-warn">⚠️ {{ t.emptyColumns }}</div>
    </div>
    <div class="kanban-board__warnings" v-else-if="!swimlanes.length">
      <div class="kbb-warn">💡 {{ t.emptyLanes }}</div>
    </div>

    <!-- Grid -->
    <div class="kbb-scroll" v-if="workflow.length">
      <div class="kbb-grid" :style="gridStyle">
        <!-- Header -->
        <div class="kbb-corner"></div>
        <div class="kbb-col-head" v-for="col in workflow" :key="'h-' + col.id">
          <div class="kbb-col-head__name">{{ col.name || '—' }}</div>
          <div class="kbb-col-head__wip">
            <span class="kbb-col-head__wip-label">{{ t.wipLabel }}</span>
            <input
              v-if="editable"
              type="number"
              min="0"
              max="99"
              class="kbb-wip-input"
              :placeholder="t.wipPh"
              :value="columnLimits[col.id] || ''"
              @change="onSetWip(col.id, $event.target.value)"
            />
            <span v-else class="kbb-wip-value">{{ columnLimits[col.id] || '—' }}</span>
          </div>
        </div>

        <!-- Lanes (or default lane if none) -->
        <template v-if="swimlanes.length">
          <template v-for="lane in swimlanes" :key="'lane-' + lane.id">
            <div class="kbb-lane-head">
              <input
                v-if="editable"
                class="kbb-lane-head__input"
                :value="lane.name"
                @change="$emit('rename-swimlane', lane.id, $event.target.value)"
                @blur="$emit('rename-swimlane', lane.id, $event.target.value)"
              />
              <span v-else class="kbb-lane-head__name">{{ lane.name }}</span>
              <button
                v-if="editable"
                type="button"
                class="kbb-lane-head__remove"
                :title="t.removeSwimlane"
                @click="$emit('remove-swimlane', lane.id)"
              >×</button>
            </div>
            <div
              v-for="col in workflow"
              :key="'cell-' + lane.id + '-' + col.id"
              class="kbb-cell"
              :class="{ 'kbb-cell--over': isOver(col.id) }"
            >
              <KanbanCard
                v-for="card in cellCards(col.id, lane.id)"
                :key="card.id"
                :card="card"
                :classes="classes"
                :columns="workflow"
                :lanes="swimlanes"
                :editable="editable"
                :t="t"
                @save="(patch) => $emit('update-card', card.id, patch)"
                @remove="$emit('remove-card', card.id)"
              />
              <button
                v-if="editable"
                type="button"
                class="kbb-add"
                @click="beginAdd(col.id, lane.id)"
                :title="t.addCard"
              >+</button>
            </div>
          </template>
        </template>
        <template v-else>
          <div class="kbb-lane-head kbb-lane-head--default">
            <span class="kbb-lane-head__name">—</span>
          </div>
          <div
            v-for="col in workflow"
            :key="'cell-default-' + col.id"
            class="kbb-cell"
            :class="{ 'kbb-cell--over': isOver(col.id) }"
          >
            <KanbanCard
              v-for="card in cellCards(col.id, '')"
              :key="card.id"
              :card="card"
              :classes="classes"
              :columns="workflow"
              :lanes="swimlanes"
              :editable="editable"
              :t="t"
              @save="(patch) => $emit('update-card', card.id, patch)"
              @remove="$emit('remove-card', card.id)"
            />
            <button
              v-if="editable"
              type="button"
              class="kbb-add"
              @click="beginAdd(col.id, '')"
              :title="t.addCard"
            >+</button>
          </div>
        </template>
      </div>
    </div>

    <!-- Warning: cards with no position (safety) -->
    <div class="kanban-board__loose" v-if="editable && looseCards.length">
      <div class="kbb-loose__h">📌 {{ looseCards.length }}</div>
      <KanbanCard
        v-for="card in looseCards"
        :key="card.id"
        :card="card"
        :classes="classes"
        :columns="workflow"
        :lanes="swimlanes"
        :editable="editable"
        :t="t"
        @save="(patch) => $emit('update-card', card.id, patch)"
        @remove="$emit('remove-card', card.id)"
      />
    </div>

    <!-- Quick-add modal -->
    <div class="kbb-add-modal" v-if="addMode" data-html2canvas-ignore="true">
      <div class="kbb-add-modal__backdrop" @click="addMode = null"></div>
      <div class="kbb-add-modal__body">
        <div class="kbb-add-modal__h">{{ t.addCard }}</div>
        <input
          ref="addInput"
          class="kbb-add-modal__input"
          v-model="addTitle"
          :placeholder="t.cardTitle"
          @keyup.enter="confirmAdd"
        />
        <select class="kbb-add-modal__select" v-model="addClass">
          <option value="">{{ t.noClass }}</option>
          <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <div class="kbb-add-modal__actions">
          <button type="button" class="kbb-btn kbb-btn--ghost" @click="addMode = null">{{ t.cardCancel }}</button>
          <button type="button" class="kbb-btn kbb-btn--primary" :disabled="!addTitle.trim()" @click="confirmAdd">{{ t.cardSave }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import KanbanCard from './KanbanCard.vue';

export default {
  name: 'KanbanBoard',
  components: { KanbanCard },
  props: {
    workflow: { type: Array, default: () => [] },
    swimlanes: { type: Array, default: () => [] },
    classes: { type: Array, default: () => [] },
    cards: { type: Array, default: () => [] },
    columnLimits: { type: Object, default: () => ({}) },
    editable: { type: Boolean, default: false },
    t: { type: Object, required: true },
  },
  emits: ['add-swimlane', 'rename-swimlane', 'remove-swimlane', 'seed-swimlanes',
          'set-wip', 'add-card', 'update-card', 'remove-card'],
  data() {
    return {
      addMode: null,
      addTitle: '',
      addClass: '',
    };
  },
  computed: {
    gridStyle() {
      const cols = Math.max(1, this.workflow.length);
      return {
        gridTemplateColumns: `160px repeat(${cols}, minmax(200px, 1fr))`,
      };
    },
    cardCountByColumn() {
      const map = {};
      for (const c of this.cards) {
        const id = c.column_id || '';
        map[id] = (map[id] || 0) + 1;
      }
      return map;
    },
    looseCards() {
      const colSet = new Set(this.workflow.map(w => w.id));
      return this.cards.filter(c => !c.column_id || !colSet.has(c.column_id));
    },
  },
  methods: {
    cellCards(columnId, laneId) {
      return this.cards.filter(c => c.column_id === columnId && (c.lane_id || '') === (laneId || ''));
    },
    isOver(columnId) {
      const limit = this.columnLimits[columnId];
      if (!limit) return false;
      return (this.cardCountByColumn[columnId] || 0) > limit;
    },
    onAddSwimlane() { this.$emit('add-swimlane', ''); },
    onSetWip(colId, val) { this.$emit('set-wip', colId, val); },
    beginAdd(colId, laneId) {
      this.addMode = { column_id: colId, lane_id: laneId };
      this.addTitle = '';
      this.addClass = '';
      this.$nextTick(() => { if (this.$refs.addInput) this.$refs.addInput.focus(); });
    },
    confirmAdd() {
      if (!this.addTitle.trim() || !this.addMode) return;
      this.$emit('add-card', {
        title: this.addTitle.trim(),
        column_id: this.addMode.column_id,
        lane_id: this.addMode.lane_id,
        class_id: this.addClass || '',
      });
      this.addMode = null;
      this.addTitle = '';
      this.addClass = '';
    },
  },
};
</script>

<style scoped>
.kanban-board { margin-top: 14px; }
.kanban-board__toolbar { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.kanban-board__warnings { margin: 6px 0 12px; }
.kbb-warn { background: #fef3c7; color: #78350f; padding: 8px 12px; border-radius: 8px; font-size: 13px; line-height: 1.5; }

.kbb-btn { border: none; border-radius: 10px; padding: 8px 14px; font-weight: 600; font-size: 13px; cursor: pointer; font-family: inherit; }
.kbb-btn--primary { background: linear-gradient(135deg, #38bdf8, #0284c7); color: #fff; }
.kbb-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.kbb-btn--ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; }
.kbb-btn--ghost:hover { border-color: #0ea5e9; color: #0ea5e9; }

.kbb-scroll { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 14px; background: #f8fafc; padding: 10px; }
.kbb-grid { display: grid; gap: 8px; min-width: 100%; }

.kbb-corner { }
.kbb-col-head {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border: 1px solid #cbd5e1; border-radius: 10px;
  padding: 8px 10px; display: flex; flex-direction: column; gap: 4px;
}
.kbb-col-head__name { font-weight: 700; color: #0f172a; font-size: 14px; }
.kbb-col-head__wip { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #475569; }
.kbb-col-head__wip-label { color: #64748b; }
.kbb-wip-input { width: 48px; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; background: #fff; font-family: inherit; text-align: center; }
.kbb-wip-value { font-weight: 700; color: #0f172a; }

.kbb-lane-head {
  background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px;
  padding: 10px; display: flex; align-items: center; gap: 4px; min-height: 80px;
}
.kbb-lane-head__input {
  flex: 1; padding: 6px 8px; border: 1px solid transparent;
  background: transparent; font-weight: 700; color: #0f172a; font-size: 14px;
  border-radius: 6px; font-family: inherit; min-width: 0;
}
.kbb-lane-head__input:focus { background: #fff; border-color: #0ea5e9; outline: none; }
.kbb-lane-head__name { font-weight: 700; color: #0f172a; font-size: 14px; flex: 1; padding: 6px 8px; }
.kbb-lane-head__remove {
  border: 1px solid transparent; background: transparent; color: #94a3b8;
  width: 24px; height: 24px; border-radius: 6px; cursor: pointer; font-size: 16px;
}
.kbb-lane-head__remove:hover { color: #ef4444; border-color: #ef4444; }
.kbb-lane-head--default { color: #94a3b8; }

.kbb-cell {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 8px; min-height: 80px; display: flex; flex-direction: column; gap: 6px;
}
.kbb-cell--over { background: #fef2f2; border-color: #fca5a5; }

.kbb-add {
  background: transparent; color: #94a3b8; border: 1px dashed #cbd5e1;
  border-radius: 8px; padding: 6px; font-size: 14px; cursor: pointer;
}
.kbb-add:hover { color: #0ea5e9; border-color: #0ea5e9; background: #f0f9ff; }

.kanban-board__loose { margin-top: 10px; padding: 10px; border: 1px dashed #fbbf24; border-radius: 10px; background: #fffbeb; }
.kbb-loose__h { font-size: 13px; font-weight: 700; color: #78350f; margin-bottom: 6px; }

.kbb-add-modal { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; }
.kbb-add-modal__backdrop { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.5); }
.kbb-add-modal__body {
  position: relative; background: #fff; border-radius: 14px; padding: 20px;
  width: min(420px, 92vw); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.3);
  display: flex; flex-direction: column; gap: 10px;
}
.kbb-add-modal__h { font-weight: 700; font-size: 16px; color: #0f172a; }
.kbb-add-modal__input, .kbb-add-modal__select {
  width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px;
  font-size: 14px; font-family: inherit; box-sizing: border-box; background: #fff; color: #0f172a;
}
.kbb-add-modal__actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>

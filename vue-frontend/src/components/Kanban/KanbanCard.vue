<template>
  <div
    class="kbc-card"
    :style="{ borderLeftColor: accent }"
    :class="{ 'kbc-card--open': editing }"
  >
    <div class="kbc-card__body" v-if="!editing" @click="startEdit">
      <div class="kbc-card__title">{{ card.title }}</div>
      <div class="kbc-card__meta" v-if="className">
        <span class="kbc-card__class" :style="{ background: accent }">{{ className }}</span>
      </div>
      <div class="kbc-card__note" v-if="card.note">{{ card.note }}</div>
    </div>

    <div class="kbc-card__edit" v-else data-html2canvas-ignore="true">
      <input class="kbc-input" v-model="draft.title" :placeholder="t.cardTitle" />
      <select class="kbc-input" v-model="draft.column_id">
        <option value="">—</option>
        <option v-for="c in columns" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select class="kbc-input" v-if="lanes.length" v-model="draft.lane_id">
        <option value="">—</option>
        <option v-for="l in lanes" :key="l.id" :value="l.id">{{ l.name }}</option>
      </select>
      <select class="kbc-input" v-model="draft.class_id">
        <option value="">{{ t.noClass }}</option>
        <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <textarea class="kbc-input" rows="2" v-model="draft.note" :placeholder="t.cardNote" />
      <div class="kbc-card__actions">
        <button type="button" class="kbc-btn kbc-btn--danger" @click="onRemove">🗑</button>
        <span style="flex: 1"></span>
        <button type="button" class="kbc-btn kbc-btn--ghost" @click="cancel">{{ t.cardCancel }}</button>
        <button type="button" class="kbc-btn kbc-btn--primary" @click="save">{{ t.cardSave }}</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'KanbanCard',
  props: {
    card: { type: Object, required: true },
    classes: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    lanes: { type: Array, default: () => [] },
    editable: { type: Boolean, default: false },
    t: { type: Object, required: true },
  },
  emits: ['save', 'remove'],
  data() {
    return {
      editing: false,
      draft: { title: '', column_id: '', lane_id: '', class_id: '', note: '' },
    };
  },
  computed: {
    classObj() { return this.classes.find(c => c.id === this.card.class_id) || null; },
    className() { return this.classObj ? this.classObj.name : ''; },
    accent() { return this.classObj ? this.classObj.color : '#94a3b8'; },
  },
  methods: {
    startEdit() {
      if (!this.editable) return;
      this.draft = {
        title: this.card.title || '',
        column_id: this.card.column_id || '',
        lane_id: this.card.lane_id || '',
        class_id: this.card.class_id || '',
        note: this.card.note || '',
      };
      this.editing = true;
    },
    cancel() { this.editing = false; },
    save() {
      this.$emit('save', {
        title: (this.draft.title || '').trim(),
        column_id: this.draft.column_id || '',
        lane_id: this.draft.lane_id || '',
        class_id: this.draft.class_id || '',
        note: (this.draft.note || '').trim(),
      });
      this.editing = false;
    },
    onRemove() { this.$emit('remove'); this.editing = false; },
  },
};
</script>

<style scoped>
.kbc-card {
  background: #fff; border: 1px solid #e2e8f0;
  border-left: 4px solid #94a3b8;
  border-radius: 8px; padding: 8px 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  cursor: pointer; transition: all 0.15s ease;
  font-size: 13px;
}
.kbc-card:hover { box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1); transform: translateY(-1px); }
.kbc-card--open { cursor: default; }
.kbc-card__title { font-weight: 600; color: #0f172a; line-height: 1.3; word-break: break-word; }
.kbc-card__meta { margin-top: 4px; display: flex; gap: 4px; flex-wrap: wrap; }
.kbc-card__class {
  padding: 1px 6px; border-radius: 999px; color: #fff;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px;
}
.kbc-card__note { margin-top: 4px; color: #64748b; font-size: 12px; line-height: 1.4; font-style: italic; }
.kbc-card__edit { display: flex; flex-direction: column; gap: 6px; }
.kbc-input {
  width: 100%; box-sizing: border-box; padding: 6px 8px;
  border: 1px solid #cbd5e1; border-radius: 6px; font-size: 12px;
  font-family: inherit; color: #0f172a; background: #fff;
}
.kbc-input:focus { outline: none; border-color: #0ea5e9; }
.kbc-card__actions { display: flex; align-items: center; gap: 4px; margin-top: 4px; }
.kbc-btn {
  border: none; border-radius: 6px; padding: 4px 10px;
  font-size: 11px; font-weight: 600; cursor: pointer; font-family: inherit;
}
.kbc-btn--primary { background: #0ea5e9; color: #fff; }
.kbc-btn--ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; }
.kbc-btn--danger { background: #fff; border: 1px solid #fca5a5; color: #ef4444; }
</style>

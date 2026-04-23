<template>
  <div class="tl">
    <ul class="tl__items" v-if="items.length">
      <li v-for="(t, idx) in items" :key="t.id" class="tl__item">
        <div class="tl__num">{{ idx + 1 }}</div>
        <div class="tl__fields">
          <input
            class="tl__title"
            type="text"
            :value="t.title"
            :placeholder="placeholder"
            @input="updateField(idx, 'title', $event.target.value)"
            @blur="normalize"
          />
          <input
            class="tl__note"
            type="text"
            :value="t.note"
            :placeholder="notePlaceholder"
            @input="updateField(idx, 'note', $event.target.value)"
            @blur="normalize"
          />
        </div>
        <button type="button" class="tl__remove" @click="remove(idx)" :title="removeLabel">×</button>
      </li>
    </ul>
    <p v-else class="tl__empty">{{ emptyHint }}</p>

    <button type="button" class="tl__add" @click="add">
      + {{ addLabel }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'TaskList',
  props: {
    tasks: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' },
    notePlaceholder: { type: String, default: '' },
    addLabel: { type: String, default: 'Add' },
    removeLabel: { type: String, default: 'Remove' },
    emptyHint: { type: String, default: '' },
  },
  data() {
    return {
      items: [],
      counter: 1,
    };
  },
  watch: {
    tasks: {
      immediate: true,
      handler(next) {
        const arr = Array.isArray(next) ? next : [];
        this.items = arr.map((t, i) => ({
          id: t.id || `local_${Date.now()}_${i}`,
          title: t.title || '',
          note: t.note || '',
        }));
        this.counter = this.items.length + 1;
      },
    },
  },
  methods: {
    add() {
      this.items.push({ id: `local_${Date.now()}_${this.counter++}`, title: '', note: '' });
      this.emit();
    },
    remove(idx) {
      this.items.splice(idx, 1);
      this.emit();
    },
    updateField(idx, key, value) {
      if (!this.items[idx]) return;
      this.items[idx] = Object.assign({}, this.items[idx], { [key]: value });
      this.emit();
    },
    normalize() {
      this.emit();
    },
    emit() {
      const clean = this.items
        .map(t => ({ id: t.id, title: (t.title || '').trim(), note: (t.note || '').trim() }))
        .filter(t => t.title);
      this.$emit('update:tasks', clean);
    },
  },
};
</script>

<style scoped>
.tl__items {
  list-style: none; padding: 0; margin: 12px 0 10px;
  display: grid; gap: 8px;
}
.tl__item {
  display: grid; grid-template-columns: 28px 1fr 28px;
  gap: 8px; align-items: center;
  background: #f8fafc; border: 1px solid #e2e8f0;
  padding: 8px 10px; border-radius: 10px;
}
.tl__num {
  width: 24px; height: 24px; border-radius: 50%;
  background: #7c3aed; color: #fff; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px;
}
.tl__fields { display: grid; gap: 4px; }
.tl__title, .tl__note {
  width: 100%; padding: 6px 8px; border: 1px solid #cbd5e1;
  border-radius: 6px; font-size: 13px; font-family: inherit;
  color: #0f172a; background: #fff; box-sizing: border-box;
}
.tl__note { font-size: 12px; color: #475569; }
.tl__title:focus, .tl__note:focus {
  outline: none; border-color: #7c3aed; box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
}
.tl__remove {
  width: 28px; height: 28px; border: none; border-radius: 50%;
  background: #fee2e2; color: #b91c1c; font-size: 18px; cursor: pointer;
  line-height: 1;
}
.tl__remove:hover { background: #fecaca; }
.tl__add {
  background: transparent; border: 1px dashed #c4b5fd; color: #7c3aed;
  padding: 8px 14px; border-radius: 8px; cursor: pointer;
  font-weight: 600; font-size: 13px;
}
.tl__add:hover { background: #faf5ff; }
.tl__empty { font-size: 13px; color: #94a3b8; margin: 10px 0; }
</style>

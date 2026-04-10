<template>
  <li class="mtp-node">
    <div class="mtp-node-row">
      <button v-if="hasChildren" type="button" class="mtp-toggle" @click="$emit('toggle', node.id)">
        {{ isExpanded ? "▾" : "▸" }}
      </button>
      <span v-else class="mtp-leaf-dot">•</span>
      <span class="mtp-node-label">{{ label }}</span>
      <template v-if="selectable">
        <span class="mtp-actions">
          <button type="button" class="mtp-select-btn" :class="{ active: selectedIdA === node.id }" @click="$emit('select-a', node.id)">A</button>
          <button type="button" class="mtp-select-btn" :class="{ active: selectedIdB === node.id }" @click="$emit('select-b', node.id)">B</button>
        </span>
      </template>
    </div>
    <ul v-if="hasChildren && isExpanded" class="mtp-children">
      <MetricsTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :expanded-map="expandedMap"
        :selected-id-a="selectedIdA"
        :selected-id-b="selectedIdB"
        :selectable="selectable"
        :ui-lang="uiLang"
        @toggle="$emit('toggle', $event)"
        @select-a="$emit('select-a', $event)"
        @select-b="$emit('select-b', $event)"
      />
    </ul>
  </li>
</template>

<script>
export default {
  name: "MetricsTreeNode",
  props: {
    node: { type: Object, required: true },
    expandedMap: { type: Object, required: true },
    selectedIdA: { type: String, default: "" },
    selectedIdB: { type: String, default: "" },
    selectable: { type: Boolean, default: true },
    uiLang: { type: String, default: "ru" },
  },
  emits: ["toggle", "select-a", "select-b"],
  computed: {
    hasChildren() {
      return Array.isArray(this.node.children) && this.node.children.length > 0;
    },
    isExpanded() {
      return !!this.expandedMap[this.node.id];
    },
    label() {
      if (this.uiLang === "en") return this.node.name || "";
      return (this.node.nameRu || this.node.name || "").trim();
    },
  },
};
</script>

<style scoped>
.mtp-node,
.mtp-children {
  list-style: none;
  margin: 0;
  padding-left: 12px;
}

.mtp-node {
  margin: 3px 0;
}

.mtp-node-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 26px;
  flex-wrap: wrap;
}

.mtp-toggle {
  all: unset;
  box-sizing: border-box !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px !important;
  height: 20px !important;
  min-width: 20px !important;
  min-height: 20px !important;
  border-radius: 6px !important;
  border: 1px solid #cfdbf2 !important;
  background: #eef4ff !important;
  color: #1e3a8a !important;
  line-height: 1;
  cursor: pointer !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
  transform: none !important;
}

.mtp-leaf-dot {
  width: 20px;
  text-align: center;
  color: #94a3b8;
}

.mtp-node-label {
  font-size: 14px;
  line-height: 1.35;
  color: #0f172a;
  flex: 1 1 260px;
  min-width: 220px;
}

.mtp-actions {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  margin-left: auto;
}

.mtp-select-btn {
  all: unset;
  box-sizing: border-box !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px !important;
  height: 24px !important;
  min-width: 24px !important;
  min-height: 24px !important;
  border-radius: 7px !important;
  border: 1px solid #c8d3eb !important;
  background: #fff !important;
  color: #1e3a8a !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  line-height: 1;
  cursor: pointer !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
  transform: none !important;
}

.mtp-select-btn.active {
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
  color: #fff !important;
}
</style>

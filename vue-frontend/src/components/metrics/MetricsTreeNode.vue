<template>
  <li class="mtp-node">
    <div class="mtp-node-row">
      <button v-if="hasChildren" type="button" class="mtp-toggle" @click="$emit('toggle', node.id)">
        {{ isExpanded ? "▾" : "▸" }}
      </button>
      <span v-else class="mtp-leaf-dot">•</span>
      <span class="mtp-node-label">{{ label }}</span>
      <template v-if="selectable">
        <button type="button" class="mtp-select-btn" :class="{ active: selectedIdA === node.id }" @click="$emit('select-a', node.id)">A</button>
        <button type="button" class="mtp-select-btn" :class="{ active: selectedIdB === node.id }" @click="$emit('select-b', node.id)">B</button>
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
      return `${this.node.name}${this.node.nameRu ? ` (${this.node.nameRu})` : ""}`;
    },
  },
};
</script>

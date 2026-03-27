<template>
  <section class="metrics-tree-panel" :class="{ compact }">
    <header class="mtp-head">
      <h3>{{ title }}</h3>
      <p class="mtp-sub">PROFIT -> Revenue/Costs -> delivery and team metrics</p>
    </header>

    <div class="mtp-controls">
      <input
        v-model.trim="searchQuery"
        class="mtp-input"
        type="text"
        placeholder="Поиск метрики (например: Lead Time, MTTR, Velocity)"
      />
      <button type="button" class="mtp-btn" @click="expandAll">Развернуть все</button>
      <button type="button" class="mtp-btn" @click="collapseAll">Свернуть все</button>
    </div>

    <div class="mtp-tree-wrap">
      <ul class="mtp-tree">
        <MetricsTreeNode
          :node="filteredTree"
          :expanded-map="expandedMap"
          :selectable="true"
          :selected-id-a="selectedMetricA"
          :selected-id-b="selectedMetricB"
          @toggle="toggleNode"
          @select-a="selectedMetricA = $event"
          @select-b="selectedMetricB = $event"
        />
      </ul>
    </div>

    <div class="mtp-ai-grid">
      <div class="mtp-ai-card">
        <h4>Разъяснение метрики</h4>
        <label class="mtp-label">Метрика</label>
        <select v-model="selectedMetricA" class="mtp-input">
          <option value="">Выберите метрику…</option>
          <option v-for="m in metricOptions" :key="m.id" :value="m.id">
            {{ optionLabel(m) }}
          </option>
        </select>
        <button type="button" class="mtp-btn mtp-btn-primary" :disabled="aiLoadingExplain || !selectedMetricA" @click="askExplainMetric">
          {{ aiLoadingExplain ? "Обработка..." : "Разъяснить метрику" }}
        </button>
        <div v-if="explainResult" class="mtp-ai-result">{{ explainResult }}</div>
      </div>

      <div class="mtp-ai-card">
        <h4>Связь между метриками</h4>
        <label class="mtp-label">Метрика A</label>
        <select v-model="selectedMetricA" class="mtp-input">
          <option value="">Выберите метрику…</option>
          <option v-for="m in metricOptions" :key="'a-' + m.id" :value="m.id">
            {{ optionLabel(m) }}
          </option>
        </select>
        <label class="mtp-label">Метрика B</label>
        <select v-model="selectedMetricB" class="mtp-input">
          <option value="">Выберите метрику…</option>
          <option v-for="m in metricOptions" :key="'b-' + m.id" :value="m.id">
            {{ optionLabel(m) }}
          </option>
        </select>
        <button
          type="button"
          class="mtp-btn mtp-btn-primary"
          :disabled="aiLoadingRel || !selectedMetricA || !selectedMetricB || selectedMetricA === selectedMetricB"
          @click="askRelationship"
        >
          {{ aiLoadingRel ? "Обработка..." : "Пояснить связь" }}
        </button>
        <div v-if="relationshipResult" class="mtp-ai-result">{{ relationshipResult }}</div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from "axios";
import { METRICS_TREE, flattenMetricsTree } from "@/constants/metricsTree";
import MetricsTreeNode from "@/components/metrics/MetricsTreeNode.vue";

function cloneWithFilter(node, query) {
  const full = `${node.name} ${node.nameRu || ""}`.toLowerCase();
  const selfMatch = !query || full.includes(query);
  const children = (node.children || [])
    .map((child) => cloneWithFilter(child, query))
    .filter(Boolean);
  if (!selfMatch && !children.length) return null;
  return { ...node, children };
}

function buildExpandedMap(node, map) {
  map[node.id] = true;
  for (const child of node.children || []) buildExpandedMap(child, map);
}

export default {
  name: "MetricsTreePanel",
  components: { MetricsTreeNode },
  props: {
    title: { type: String, default: "Древо метрик" },
    surveyToken: { type: String, default: "" },
    compact: { type: Boolean, default: false },
  },
  data() {
    const initialExpanded = {};
    buildExpandedMap(METRICS_TREE, initialExpanded);
    return {
      tree: METRICS_TREE,
      searchQuery: "",
      expandedMap: initialExpanded,
      selectedMetricA: "",
      selectedMetricB: "",
      aiLoadingExplain: false,
      aiLoadingRel: false,
      explainResult: "",
      relationshipResult: "",
    };
  },
  computed: {
    filteredTree() {
      const query = (this.searchQuery || "").toLowerCase();
      return cloneWithFilter(this.tree, query) || this.tree;
    },
    metricOptions() {
      return flattenMetricsTree(this.tree).filter((m) => m.level > 0);
    },
    metricsById() {
      return Object.fromEntries(this.metricOptions.map((m) => [m.id, m]));
    },
  },
  methods: {
    optionLabel(m) {
      return `${"  ".repeat(Math.max(0, m.level - 1))}${m.name}${m.nameRu ? ` (${m.nameRu})` : ""}`;
    },
    toggleNode(id) {
      this.expandedMap = { ...this.expandedMap, [id]: !this.expandedMap[id] };
    },
    expandAll() {
      const map = {};
      buildExpandedMap(this.tree, map);
      this.expandedMap = map;
    },
    collapseAll() {
      this.expandedMap = { [this.tree.id]: true };
    },
    async askExplainMetric() {
      if (!this.selectedMetricA) return;
      const metric = this.metricsById[this.selectedMetricA];
      this.aiLoadingExplain = true;
      this.explainResult = "";
      try {
        const payload = {
          metric_key: metric.id,
          metric_name: metric.name,
          metric_name_ru: metric.nameRu || "",
          context: "metrics_tree",
        };
        if (this.surveyToken) payload.survey_token = this.surveyToken;
        const res = await axios.post("/api/metrics-tree/explain", payload, this.surveyToken ? undefined : { headers: this.authHeaders() });
        this.explainResult = res.data.content || "Нет данных";
      } catch (e) {
        this.explainResult = `Ошибка: ${e.response?.data?.error || "Сервис недоступен"}`;
      } finally {
        this.aiLoadingExplain = false;
      }
    },
    async askRelationship() {
      if (!this.selectedMetricA || !this.selectedMetricB || this.selectedMetricA === this.selectedMetricB) return;
      const a = this.metricsById[this.selectedMetricA];
      const b = this.metricsById[this.selectedMetricB];
      this.aiLoadingRel = true;
      this.relationshipResult = "";
      try {
        const payload = {
          metric_a_key: a.id,
          metric_a_name: a.name,
          metric_a_name_ru: a.nameRu || "",
          metric_b_key: b.id,
          metric_b_name: b.name,
          metric_b_name_ru: b.nameRu || "",
        };
        if (this.surveyToken) payload.survey_token = this.surveyToken;
        const res = await axios.post("/api/metrics-tree/relationship", payload, this.surveyToken ? undefined : { headers: this.authHeaders() });
        this.relationshipResult = res.data.content || "Нет данных";
      } catch (e) {
        this.relationshipResult = `Ошибка: ${e.response?.data?.error || "Сервис недоступен"}`;
      } finally {
        this.aiLoadingRel = false;
      }
    },
    authHeaders() {
      const token = localStorage.getItem("token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
  },
};
</script>

<style scoped>
.metrics-tree-panel {
  border: 1px solid #dbe5f3;
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, #ffffff, #f7faff);
}
.mtp-head h3 { margin: 0; }
.mtp-sub { margin: 6px 0 0; color: #64748b; font-size: 12px; }
.mtp-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.mtp-input {
  border: 1px solid #d7dfef;
  border-radius: 10px;
  padding: 8px 10px;
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
  background: #fbfdff;
}
.mtp-btn {
  all: unset;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d7dfef;
  border-radius: 10px;
  background: #fff;
  padding: 6px 11px;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  line-height: 1.1;
  color: #0f172a;
}
.mtp-btn-primary {
  background: linear-gradient(145deg, #1d4ed8, #2563eb);
  color: #fff;
  border-color: #1d4ed8;
}
.mtp-btn:disabled { opacity: 0.6; cursor: wait; }
.mtp-tree-wrap {
  margin-top: 10px;
  max-height: 360px;
  overflow: auto;
  border: 1px solid #e7ecf6;
  border-radius: 12px;
  padding: 8px;
  background: #fff;
}
.mtp-tree { list-style: none; padding-left: 8px; margin: 0; }
.mtp-ai-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}
.mtp-ai-card {
  border: 1px solid #e1e8f7;
  border-radius: 12px;
  background: #fff;
  padding: 10px;
}
.mtp-ai-card h4 { margin: 0 0 8px; }
.mtp-label { font-size: 12px; font-weight: 700; color: #475569; display: block; margin: 6px 0 4px; }
.mtp-ai-result {
  margin-top: 8px;
  padding: 8px;
  border-radius: 8px;
  background: #f1f5ff;
  color: #1e3a8a;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.45;
}
</style>

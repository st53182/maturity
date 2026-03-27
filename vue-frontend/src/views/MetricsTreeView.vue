<template>
  <div class="metrics-tree-view">
    <MetricsTreePanel title="Древо метрик продукта и поставки" />
  </div>
</template>

<script>
import MetricsTreePanel from "@/components/metrics/MetricsTreePanel.vue";

export default {
  name: "MetricsTreeView",
  components: { MetricsTreePanel },
};
</script>

<style scoped>
.metrics-tree-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 0 30px;
}
</style>

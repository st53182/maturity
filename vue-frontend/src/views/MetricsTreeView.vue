<template>
  <div class="metrics-tree-view">
    <MetricsTreePanel :title="$t('metricsTree.pageTitleLong')" :ui-lang="surveyLang" />
  </div>
</template>

<script>
import MetricsTreePanel from "@/components/metrics/MetricsTreePanel.vue";

export default {
  name: "MetricsTreeView",
  components: { MetricsTreePanel },
  computed: {
    surveyLang() {
      try {
        const loc = this.$i18n?.locale;
        const s = typeof loc === "string" ? loc : loc?.value;
        return s === "en" ? "en" : "ru";
      } catch {
        return typeof localStorage !== "undefined" && localStorage.getItem("language") === "en" ? "en" : "ru";
      }
    },
  },
};
</script>

<style scoped>
.metrics-tree-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 0 30px;
}
</style>

<template>
  <NewToolShell v-if="config" :title="title">
    <component :is="asyncComp" />
  </NewToolShell>
  <div v-else class="new-tool-shell-error" role="alert">{{ $t("common.error") }}: {{ $t("common.notFound") }}</div>
</template>

<script>
import { defineAsyncComponent, markRaw } from "vue";
import NewToolShell from "./NewToolShell.vue";

const TOOL_MAP = {
  conflicts: {
    loader: () => import("@/views/ConflictResolution.vue"),
    titleKey: "nav.conflicts",
  },
  profile: {
    loader: () => import("@/views/UserProfile.vue"),
    titleKey: "nav.profile",
  },
  surveys: {
    loader: () => import("@/views/Surveys.vue"),
    titleKey: "nav.surveys",
  },
  "backlog-prep": {
    loader: () => import("@/views/BacklogPrep.vue"),
    titleKey: "nav.backlogPrep",
  },
  "system-thinking": {
    loader: () => import("@/views/SystemThinkingIceberg.vue"),
    titleKey: "newHome.links.systemThinking",
  },
  "agile-kata": {
    loader: () => import("@/views/AgileKataCanvas.vue"),
    titleKey: "nav.agileKata",
  },
  "agile-tools": {
    loader: () => import("@/views/AgileTools.vue"),
    titleKey: "nav.agileTools",
  },
  "meeting-design": {
    loader: () => import("@/views/MeetingDesign.vue"),
    titleKey: "nav.meetingDesign",
  },
  motivation: {
    loader: () => import("@/views/UserMotivation.vue"),
    titleKey: "nav.motivation",
  },
  "project-card": {
    loader: () => import("@/views/ProjectManagementCard.vue"),
    titleKey: "nav.projectCard",
  },
};

export default {
  name: "NewWrappedTool",
  components: { NewToolShell },
  props: {
    toolId: {
      type: String,
      required: true,
    },
  },
  data() {
    return { asyncComp: null };
  },
  computed: {
    config() {
      return TOOL_MAP[this.toolId] || null;
    },
    title() {
      if (!this.config) return "";
      return this.$t(this.config.titleKey);
    },
  },
  watch: {
    toolId: {
      immediate: true,
      handler(id) {
        const cfg = TOOL_MAP[id];
        this.asyncComp = cfg
          ? markRaw(
              defineAsyncComponent({
                loader: cfg.loader,
                delay: 80,
              })
            )
          : null;
      },
    },
  },
};
</script>

<style scoped>
.new-tool-shell-error {
  padding: 2rem;
  text-align: center;
  color: #c00;
}
</style>

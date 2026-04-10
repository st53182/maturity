<template>
  <NewToolShell :title="$t('newUi.dashboardTitle')" :subtitle="$t('newUi.dashboardSubtitle')">
    <div class="new-dash-interview-banner" role="region" :aria-label="$t('nav.interviewSimulator')">
      <p class="new-dash-interview-banner__text">{{ $t('newUi.dashboardInterviewBanner') }}</p>
      <router-link to="/new/interview-simulator" class="new-dash-interview-banner__cta">
        {{ $t('newUi.dashboardInterviewCta') }} →
      </router-link>
    </div>
    <div class="new-shell__content">
      <UserDashboard variant="new" />
    </div>
  </NewToolShell>
</template>

<script>
import UserDashboard from "@/views/UserDashboard.vue";
import NewToolShell from "@/views/NewToolShell.vue";

export default {
  components: { UserDashboard, NewToolShell },
};
</script>

<style scoped>
.new-dash-interview-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px 16px;
  margin-bottom: 20px;
  padding: 14px 18px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(20, 43, 102, 0.06), rgba(39, 84, 199, 0.1));
  border: 1px solid rgba(39, 84, 199, 0.2);
}
.new-dash-interview-banner__text {
  margin: 0;
  flex: 1;
  min-width: 200px;
  font-size: 0.95rem;
  line-height: 1.45;
  color: var(--vl-text, #0d1733);
}
.new-dash-interview-banner__cta {
  font-weight: 600;
  font-size: 0.9rem;
  color: #2754c7;
  text-decoration: none;
  white-space: nowrap;
}
.new-dash-interview-banner__cta:hover {
  text-decoration: underline;
}
.new-shell__content {
  margin-top: 0;
}
</style>


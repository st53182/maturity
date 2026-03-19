<template>
  <NewToolShell :title="$t('newUi.dashboardTitle')" :subtitle="$t('newUi.dashboardSubtitle')">
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
.new-shell__content {
  margin-top: 0;
}
</style>


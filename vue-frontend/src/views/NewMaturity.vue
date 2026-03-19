<template>
  <NewToolShell :title="$t('newUi.maturityTitle')" :subtitle="$t('newUi.maturitySubtitle')">
    <div class="new-shell__content">
      <CreateMaturityLink />
    </div>
  </NewToolShell>
</template>

<script>
import CreateMaturityLink from "@/views/CreateMaturityLink.vue";
import NewToolShell from "@/views/NewToolShell.vue";

export default {
  components: { CreateMaturityLink, NewToolShell },
};
</script>

<style scoped>
.new-shell__content {
  margin-top: 0;
}
</style>


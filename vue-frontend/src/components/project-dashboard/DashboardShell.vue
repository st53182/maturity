<template>
  <div class="gb-shell flex flex-col h-[calc(100vh-2.5rem)] min-h-[560px] max-h-[calc(100dvh-2rem)] bg-gb-soft rounded-xl border border-gb-border overflow-hidden">
    <slot name="top" />
    <slot name="summary" />
    <div class="flex flex-1 min-h-0">
      <aside class="gb-shell__side w-[220px] shrink-0 border-r border-gb-border bg-gb-surface overflow-y-auto hidden lg:block">
        <slot name="sidebar" />
      </aside>
      <div class="flex flex-col flex-1 min-w-0 min-h-0">
        <slot name="filters" />
        <main class="flex-1 min-h-0 overflow-hidden relative bg-gb-surface">
          <slot />
        </main>
      </div>
      <slot name="drawer" />
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
@media (max-width: 1023px) {
  .gb-shell__side {
    display: none;
  }
}
</style>

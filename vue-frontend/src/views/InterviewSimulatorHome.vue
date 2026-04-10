<template>
  <div class="is-page">
    <header class="is-page__header">
      <router-link to="/new" class="is-page__back">{{ $t('interviewSimulator.backToGrowboard') }}</router-link>
      <h1>{{ $t('interviewSimulator.homeTitle') }}</h1>
      <p class="is-page__lead">
        {{ $t('interviewSimulator.homeLead') }}
      </p>
      <div class="is-page__cta">
        <router-link to="/new/interview-simulator/setup" class="is-btn is-btn--primary">{{
          $t('interviewSimulator.configureInterview')
        }}</router-link>
        <router-link to="/new/dashboard" class="is-btn is-btn--ghost">{{ $t('nav.dashboard') }}</router-link>
      </div>
    </header>
    <section class="is-page__grid">
      <div class="is-card-lite">
        <h2>{{ $t('interviewSimulator.howItWorks') }}</h2>
        <ol>
          <li>{{ $t('interviewSimulator.step1') }}</li>
          <li>{{ $t('interviewSimulator.step2') }}</li>
          <li>{{ $t('interviewSimulator.step3') }}</li>
        </ol>
      </div>
      <div class="is-card-lite">
        <h2>{{ $t('interviewSimulator.voiceSectionTitle') }}</h2>
        <p>{{ $t('interviewSimulator.voiceSectionBody') }}</p>
      </div>
    </section>
  </div>
</template>

<script>
export default { name: 'InterviewSimulatorHome' };
</script>

<style scoped>
.is-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 20px 48px;
  text-align: left;
}
.is-page__header h1 {
  margin: 12px 0 12px;
  font-size: 1.75rem;
  color: var(--vl-text, #0d1733);
}
.is-page__back {
  font-size: 0.9rem;
  color: #2754c7;
  text-decoration: none;
}
.is-page__lead {
  color: var(--vl-muted, #5d6b8a);
  line-height: 1.55;
  margin-bottom: 20px;
}
.is-page__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.is-btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.9rem;
}
.is-btn--primary {
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
}
.is-btn--ghost {
  border: 1px solid var(--vl-border, #d8e0f0);
  color: var(--vl-text, #0d1733);
}
.is-page__grid {
  display: grid;
  gap: 16px;
  margin-top: 32px;
}
.is-card-lite {
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 16px;
  padding: 20px;
  background: #fff;
}
.is-card-lite h2 {
  margin: 0 0 10px;
  font-size: 1.05rem;
}
.is-card-lite ol,
.is-card-lite p {
  margin: 0;
  color: var(--vl-text, #0d1733);
  line-height: 1.5;
  font-size: 0.9rem;
}
.is-card-lite ol {
  padding-left: 1.2rem;
}
</style>

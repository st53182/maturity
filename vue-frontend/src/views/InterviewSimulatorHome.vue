<template>
  <div class="is-page">
    <header class="is-page__header">
      <router-link to="/new" class="is-page__back">← GrowBoard</router-link>
      <h1>AI Interview Simulator</h1>
      <p class="is-page__lead">
        Practice a structured technical interview for your role and level. Optionally paste a real job description so
        questions and feedback align with that vacancy.
      </p>
      <div class="is-page__cta">
        <router-link to="/new/interview-simulator/setup" class="is-btn is-btn--primary">Configure interview</router-link>
        <router-link to="/new/dashboard" class="is-btn is-btn--ghost">Dashboard</router-link>
      </div>
    </header>
    <section class="is-page__grid">
      <div class="is-card-lite">
        <h2>How it works</h2>
        <ol>
          <li>Pick role & seniority (and optional JD).</li>
          <li>Answer 7–13 interviewer turns (including follow-ups).</li>
          <li>Receive a detailed report: strengths, gaps, vacancy fit.</li>
        </ol>
      </div>
      <div class="is-card-lite">
        <h2>Voice</h2>
        <p>MVP is text-first. Hooks for speech-to-text and TTS are reserved in the codebase for a later iteration.</p>
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

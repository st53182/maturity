<template>
  <article v-if="report" class="is-fb">
    <h2 class="is-fb__title">{{ $t('interviewSimulator.feedbackTitle') }}</h2>
    <p class="is-fb__score">
      {{ $t('interviewSimulator.overallScore') }} <strong>{{ report.overall_score }}</strong> {{ $t('interviewSimulator.outOf100') }}
    </p>
    <p class="is-fb__summary">{{ report.summary }}</p>
    <div v-if="report.vacancy_fit" class="is-fb__fit">
      <h3>{{ $t('interviewSimulator.vacancyFit') }}</h3>
      <p>
        <strong>{{ report.vacancy_fit.match_percent }}%</strong> —
        {{ report.vacancy_fit.summary }}
      </p>
      <div class="is-fb__cols">
        <div>
          <h4>{{ $t('interviewSimulator.coveredWell') }}</h4>
          <ul>
            <li v-for="(x, i) in report.vacancy_fit.requirements_covered_well" :key="'w' + i">{{ x }}</li>
          </ul>
        </div>
        <div>
          <h4>{{ $t('interviewSimulator.gaps') }}</h4>
          <ul>
            <li v-for="(x, i) in report.vacancy_fit.requirements_gaps" :key="'g' + i">{{ x }}</li>
          </ul>
        </div>
      </div>
      <h4>{{ $t('interviewSimulator.topicsToStudy') }}</h4>
      <ul>
        <li v-for="(x, i) in report.vacancy_fit.topics_to_study" :key="'t' + i">{{ x }}</li>
      </ul>
    </div>
    <h3>{{ $t('interviewSimulator.strengths') }}</h3>
    <ul>
      <li v-for="(s, i) in report.strengths" :key="'s' + i">{{ s }}</li>
    </ul>
    <h3>{{ $t('interviewSimulator.weaknesses') }}</h3>
    <ul>
      <li v-for="(w, i) in report.weaknesses" :key="'wk' + i">{{ w }}</li>
    </ul>
    <h3>{{ $t('interviewSimulator.recommendations') }}</h3>
    <ul>
      <li v-for="(r, i) in report.recommendations" :key="'r' + i">{{ r }}</li>
    </ul>
    <h3>{{ $t('interviewSimulator.exampleStrongAnswer') }}</h3>
    <blockquote class="is-fb__quote">{{ report.example_strong_answer }}</blockquote>
  </article>
</template>

<script>
export default {
  name: 'FeedbackCard',
  props: {
    report: { type: Object, default: null },
  },
};
</script>

<style scoped>
.is-fb {
  background: #fff;
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 16px;
  padding: 24px;
  text-align: left;
}
.is-fb__title {
  margin: 0 0 8px;
  font-size: 1.35rem;
  color: var(--vl-text, #0d1733);
}
.is-fb__score {
  margin: 0 0 16px;
  font-size: 1rem;
  color: var(--vl-muted, #5d6b8a);
}
.is-fb__score strong {
  color: #2754c7;
  font-size: 1.2rem;
}
.is-fb__summary {
  line-height: 1.55;
  color: var(--vl-text, #0d1733);
  margin-bottom: 20px;
}
.is-fb h3 {
  margin: 20px 0 8px;
  font-size: 1rem;
  color: var(--vl-text, #0d1733);
}
.is-fb h4 {
  margin: 12px 0 6px;
  font-size: 0.85rem;
  color: var(--vl-muted, #5d6b8a);
}
.is-fb ul {
  margin: 0;
  padding-left: 1.2rem;
  color: var(--vl-text, #0d1733);
  line-height: 1.5;
}
.is-fb__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 640px) {
  .is-fb__cols {
    grid-template-columns: 1fr;
  }
}
.is-fb__fit {
  padding: 16px;
  border-radius: 12px;
  background: #f6f9ff;
  border: 1px solid rgba(39, 84, 199, 0.15);
  margin-bottom: 8px;
}
.is-fb__quote {
  margin: 0;
  padding: 12px 16px;
  border-left: 4px solid #2754c7;
  background: #f6f9ff;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--vl-text, #0d1733);
}
</style>

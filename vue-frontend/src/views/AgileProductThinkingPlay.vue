<template>
  <div class="pt-play modern-ui" ref="pdfRoot">
    <header class="pt-play__head">
      <div class="pt-play__lang">
        <button type="button" :class="{ active: locale === 'ru' }" @click="switchLang('ru')">RU</button>
        <button type="button" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
      </div>
      <h1 class="pt-play__title">{{ $t('agileTraining.productThinking.playTitle') }}</h1>
      <div class="pt-play__meta">
        <span class="pt-play__step">
          {{ $t('agileTraining.productThinking.progress', { current: stepIndex + 1, total: totalSteps }) }}
        </span>
        <span class="pt-play__group" v-if="group">· {{ group.name }}</span>
        <span class="pt-play__save" v-if="savingState === 'saving'">· {{ $t('agileTraining.productThinking.saving') }}</span>
        <span class="pt-play__save pt-play__save--ok" v-else-if="savingState === 'saved'">· {{ $t('agileTraining.productThinking.saved') }}</span>
      </div>
      <div class="pt-play__progressbar">
        <div class="pt-play__progressbar-fill" :style="{ width: progressPct + '%' }" />
      </div>
    </header>

    <div v-if="loadError" class="pt-play__error">{{ loadError }}</div>

    <div v-else-if="loading" class="pt-play__loading">{{ $t('common.loading') }}…</div>

    <section v-else class="pt-play__stage">
      <!-- 0. Case choice -->
      <div v-if="stage === 'case_choice'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.caseChoice.title') }}</h2>
        <p class="pt-card__lead">{{ $t('agileTraining.productThinking.caseChoice.lead') }}</p>
        <div class="pt-case-grid">
          <article
            v-for="c in availableCases"
            :key="c.key"
            class="pt-case-card"
            :class="{ 'pt-case-card--active': caseKey === c.key }"
            @click="pickCase(c.key)"
          >
            <div class="pt-case-card__emoji">{{ c.emoji }}</div>
            <div class="pt-case-card__label">{{ c.label }}</div>
            <div class="pt-case-card__title">{{ c.title }}</div>
            <div class="pt-case-card__short">{{ c.short }}</div>
            <div class="pt-case-card__pick" v-if="caseKey === c.key">
              ✓ {{ $t('agileTraining.productThinking.caseChoice.picked') }}
            </div>
            <div class="pt-case-card__pick pt-case-card__pick--ghost" v-else>
              {{ $t('agileTraining.productThinking.caseChoice.pickCta') }}
            </div>
          </article>
        </div>
        <div v-if="caseKey" class="pt-note">
          👉 {{ $t('agileTraining.productThinking.caseChoice.afterPick') }}
        </div>
      </div>

      <!-- 1. Intro -->
      <div v-else-if="stage === 'intro'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.intro.title') }}</h2>
        <p class="pt-card__lead">{{ $t('agileTraining.productThinking.intro.lead') }}</p>
        <div class="pt-case" v-if="selectedCase">
          <div class="pt-case__title">{{ selectedCase.emoji }} {{ selectedCase.title }}</div>
          <div class="pt-case__block">
            <div class="pt-case__h">{{ $t('agileTraining.productThinking.case.contextTitle') }}</div>
            <ul>
              <li v-for="(line, i) in selectedCase.context" :key="i">{{ line }}</li>
            </ul>
          </div>
          <div class="pt-case__goal">👉 {{ selectedCase.goal }}</div>
          <div class="pt-case__hint">💡 {{ selectedCase.hint }}</div>
          <button
            type="button"
            class="pt-btn pt-btn--ghost pt-case__switch"
            @click="stage = 'case_choice'"
          >
            🔄 {{ $t('agileTraining.productThinking.caseChoice.switch') }}
          </button>
        </div>
        <div v-if="!participantToken" class="pt-start">
          <label class="pt-label">{{ $t('agileTraining.productThinking.nameAsk') }}</label>
          <input
            class="pt-input"
            type="text"
            v-model="displayName"
            :placeholder="$t('agileTraining.productThinking.namePlaceholder')"
          />
          <button class="pt-btn pt-btn--primary" :disabled="joining" @click="joinGroup">
            {{ $t('agileTraining.productThinking.start') }}
          </button>
          <div v-if="joinError" class="pt-error">{{ joinError }}</div>
        </div>
      </div>

      <!-- 2. Example -->
      <div v-else-if="stage === 'example'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.example.title') }}</h2>
        <p class="pt-card__lead">{{ $t('agileTraining.productThinking.example.lead') }}</p>

        <div class="pt-example-warn" v-if="selectedCase && selectedCase.examples">
          <div class="pt-example-warn__h">⚠️ {{ $t('agileTraining.productThinking.example.patternLabel') }}</div>
          <p class="pt-example-warn__p">{{ selectedCase.examples.scenario }}</p>
        </div>

        <div class="pt-compare" v-if="selectedCase && selectedCase.examples">
          <div class="pt-compare__col">
            <div class="pt-compare__h">👤 {{ $t('agileTraining.productThinking.example.userStoryLabel') }}</div>
            <p class="pt-compare__quote">«{{ selectedCase.examples.user_story }}»</p>
            <div class="pt-compare__explain" v-if="selectedCase.examples.focus_us">{{ selectedCase.examples.focus_us }}</div>
            <div class="pt-compare__explain" v-else>{{ $t('agileTraining.productThinking.example.explainUserStory') }}</div>
          </div>
          <div class="pt-compare__col">
            <div class="pt-compare__h">🎬 {{ $t('agileTraining.productThinking.example.jobStoryLabel') }}</div>
            <p class="pt-compare__quote">«{{ selectedCase.examples.job_story }}»</p>
            <div class="pt-compare__explain" v-if="selectedCase.examples.focus_js">{{ selectedCase.examples.focus_js }}</div>
            <div class="pt-compare__explain" v-else>{{ $t('agileTraining.productThinking.example.explainJobStory') }}</div>
          </div>
        </div>
        <div class="pt-note" v-if="selectedCase && selectedCase.examples && selectedCase.examples.note">👉 {{ selectedCase.examples.note }}</div>
        <p class="pt-explain">{{ $t('agileTraining.productThinking.example.explain') }}</p>
      </div>

      <!-- 3. User Story -->
      <div v-else-if="stage === 'user_story'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.userStoryScreen.title') }}</h2>
        <div class="pt-note">👉 {{ $t('agileTraining.productThinking.userStoryScreen.context') }}</div>
        <div class="pt-questions">
          <div class="pt-questions__h">{{ $t('agileTraining.productThinking.userStoryScreen.questionsTitle') }}</div>
          <ul>
            <li>{{ $t('agileTraining.productThinking.userStoryScreen.q1') }}</li>
            <li>{{ $t('agileTraining.productThinking.userStoryScreen.q2') }}</li>
            <li>{{ $t('agileTraining.productThinking.userStoryScreen.q3') }}</li>
          </ul>
        </div>
        <div class="pt-hint">
          <strong>{{ $t('agileTraining.productThinking.userStoryScreen.hintTitle') }}:</strong>
          {{ $t('agileTraining.productThinking.userStoryScreen.hint') }}
        </div>
        <textarea
          class="pt-textarea"
          rows="4"
          v-model="userStory"
          :placeholder="$t('agileTraining.productThinking.userStoryScreen.placeholder')"
          @blur="persist"
        />
        <AiHelper
          ref="aiUserStory"
          :locale="locale"
          :mode="'user_story'"
          :label="$t('agileTraining.productThinking.aiModeUserStory')"
          :calls-remaining="aiRemaining"
          :initial-input="userStory"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.productThinking.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 4. Job Story -->
      <div v-else-if="stage === 'job_story'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.jobStoryScreen.title') }}</h2>
        <div class="pt-note">👉 {{ $t('agileTraining.productThinking.jobStoryScreen.context') }}</div>
        <div class="pt-questions">
          <div class="pt-questions__h">{{ $t('agileTraining.productThinking.jobStoryScreen.questionsTitle') }}</div>
          <ul>
            <li>{{ $t('agileTraining.productThinking.jobStoryScreen.q1') }}</li>
            <li>{{ $t('agileTraining.productThinking.jobStoryScreen.q2') }}</li>
            <li>{{ $t('agileTraining.productThinking.jobStoryScreen.q3') }}</li>
          </ul>
        </div>
        <div class="pt-hint">
          <strong>{{ $t('agileTraining.productThinking.jobStoryScreen.hintTitle') }}:</strong>
          {{ $t('agileTraining.productThinking.jobStoryScreen.hint') }}
        </div>
        <textarea
          class="pt-textarea"
          rows="4"
          v-model="jobStory"
          :placeholder="$t('agileTraining.productThinking.jobStoryScreen.placeholder')"
          @blur="persist"
        />
        <AiHelper
          ref="aiJobStory"
          :locale="locale"
          :mode="'job_story'"
          :label="$t('agileTraining.productThinking.aiModeJobStory')"
          :calls-remaining="aiRemaining"
          :initial-input="jobStory"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.productThinking.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 5. Compare -->
      <div v-else-if="stage === 'compare'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.compare.title') }}</h2>
        <div class="pt-note">👉 {{ $t('agileTraining.productThinking.compare.lead') }}</div>
        <div class="pt-compare">
          <div class="pt-compare__col">
            <div class="pt-compare__h">👤 {{ $t('agileTraining.productThinking.compare.yourUserStory') }}</div>
            <p class="pt-compare__quote" v-if="userStory">«{{ userStory }}»</p>
            <p class="pt-compare__quote pt-compare__quote--empty" v-else>{{ $t('agileTraining.productThinking.compare.empty') }}</p>
          </div>
          <div class="pt-compare__col">
            <div class="pt-compare__h">🎬 {{ $t('agileTraining.productThinking.compare.yourJobStory') }}</div>
            <p class="pt-compare__quote" v-if="jobStory">«{{ jobStory }}»</p>
            <p class="pt-compare__quote pt-compare__quote--empty" v-else>{{ $t('agileTraining.productThinking.compare.empty') }}</p>
          </div>
        </div>
        <div class="pt-questions">
          <ul>
            <li>{{ $t('agileTraining.productThinking.compare.q1') }}</li>
            <li>{{ $t('agileTraining.productThinking.compare.q2') }}</li>
            <li>{{ $t('agileTraining.productThinking.compare.q3') }}</li>
          </ul>
        </div>
        <label class="pt-label">{{ $t('agileTraining.productThinking.compare.notesLabel') }}</label>
        <textarea
          class="pt-textarea"
          rows="3"
          v-model="notes.compare"
          :placeholder="$t('agileTraining.productThinking.compare.notesPlaceholder')"
          @blur="persist"
        />
      </div>

      <!-- 6. Epic -->
      <div v-else-if="stage === 'epic'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.epic.title') }}</h2>
        <p class="pt-card__lead">👉 {{ $t('agileTraining.productThinking.epic.lead') }}</p>

        <div class="pt-epic-card" v-if="selectedCase">
          <div class="pt-epic-card__label">🧱 {{ $t('agileTraining.productThinking.epic.ourEpicLabel') }}</div>
          <div class="pt-epic-card__title">{{ selectedCase.epic_summary }}</div>
          <div class="pt-epic-card__why">
            <strong>{{ $t('agileTraining.productThinking.epic.whyLabel') }}:</strong>
            {{ selectedCase.epic_why }}
          </div>
        </div>

        <div class="pt-env" v-if="selectedCase && selectedCase.environment">
          <div class="pt-env__intro">🧰 {{ $t('agileTraining.productThinking.epic.envIntro') }}</div>
          <div class="pt-env__grid">
            <section class="pt-env__block" v-if="hasEnvList('audience')">
              <div class="pt-env__h">👥 {{ $t('agileTraining.productThinking.env.audience') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.audience" :key="'aud'+i">{{ line }}</li>
              </ul>
            </section>
            <section class="pt-env__block" v-if="hasEnvList('stack')">
              <div class="pt-env__h">⚙️ {{ $t('agileTraining.productThinking.env.stack') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.stack" :key="'st'+i">{{ line }}</li>
              </ul>
            </section>
            <section class="pt-env__block" v-if="hasEnvList('architecture')">
              <div class="pt-env__h">🧩 {{ $t('agileTraining.productThinking.env.architecture') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.architecture" :key="'arc'+i">{{ line }}</li>
              </ul>
            </section>
            <section class="pt-env__block" v-if="hasEnvList('existing')">
              <div class="pt-env__h">📦 {{ $t('agileTraining.productThinking.env.existing') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.existing" :key="'ex'+i">{{ line }}</li>
              </ul>
            </section>
            <section class="pt-env__block" v-if="hasEnvList('constraints')">
              <div class="pt-env__h">🚧 {{ $t('agileTraining.productThinking.env.constraints') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.constraints" :key="'cn'+i">{{ line }}</li>
              </ul>
            </section>
            <section class="pt-env__block" v-if="hasEnvList('stakeholders')">
              <div class="pt-env__h">🤝 {{ $t('agileTraining.productThinking.env.stakeholders') }}</div>
              <ul>
                <li v-for="(line, i) in selectedCase.environment.stakeholders" :key="'sh'+i">{{ line }}</li>
              </ul>
            </section>
          </div>
          <div class="pt-env__hint">💡 {{ $t('agileTraining.productThinking.epic.envHint') }}</div>
        </div>

        <div class="pt-primer" v-if="primer.epic_text">
          <div class="pt-primer__h">💡 {{ primer.epic_title }}</div>
          <p>{{ primer.epic_text }}</p>
        </div>

        <div class="pt-epic-summary" v-if="userStory || jobStory">
          <div class="pt-epic-summary__h">📝 {{ $t('agileTraining.productThinking.epic.yourAnswersLabel') }}</div>
          <div v-if="userStory"><strong>User Story:</strong> {{ userStory }}</div>
          <div v-if="jobStory"><strong>Job Story:</strong> {{ jobStory }}</div>
        </div>
      </div>

      <!-- 7. Decomposition example -->
      <div v-else-if="stage === 'decomposition_example'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.decompositionExample.title') }}</h2>
        <p class="pt-card__lead">👉 {{ $t('agileTraining.productThinking.decompositionExample.lead') }}</p>

        <div class="pt-primer" v-if="primer.decomposition_text">
          <div class="pt-primer__h">💡 {{ primer.decomposition_title }}</div>
          <p>{{ primer.decomposition_text }}</p>
        </div>

        <div class="pt-epic-card pt-epic-card--compact" v-if="selectedCase">
          <div class="pt-epic-card__label">🧱 {{ $t('agileTraining.productThinking.epic.ourEpicLabel') }}</div>
          <div class="pt-epic-card__title">{{ selectedCase.epic_summary }}</div>
        </div>

        <div class="pt-variants" v-if="decompositionVariants.length">
          <article
            class="pt-variant"
            v-for="(variant, vi) in decompositionVariants"
            :key="vi"
          >
            <div class="pt-variant__h">{{ variant.label }}</div>
            <div class="pt-variant__sub">{{ variant.subtitle }}</div>
            <ul class="pt-steps">
              <li v-for="(step, i) in variant.items" :key="i">
                <template v-if="isStepObject(step)">
                  <span class="pt-steps__tag">{{ step.tag }}</span>
                  <span class="pt-steps__text">{{ step.text }}</span>
                </template>
                <template v-else>
                  <span class="pt-steps__num">{{ i + 1 }}</span>
                  <span>{{ step }}</span>
                </template>
              </li>
            </ul>
          </article>
        </div>

        <p class="pt-explain">{{ $t('agileTraining.productThinking.decompositionExample.compare') }}</p>
      </div>

      <!-- 8. Decomposition practice -->
      <div v-else-if="stage === 'decomposition'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.decomposition.title') }}</h2>
        <div class="pt-note">👉 {{ $t('agileTraining.productThinking.decomposition.context') }}</div>

        <div class="pt-epic-card pt-epic-card--compact" v-if="selectedCase">
          <div class="pt-epic-card__label">🧱 {{ $t('agileTraining.productThinking.epic.ourEpicLabel') }}</div>
          <div class="pt-epic-card__title">{{ selectedCase.epic_summary }}</div>
        </div>

        <div class="pt-good-bad" v-if="selectedCase">
          <div class="pt-good-bad__item pt-good-bad__item--good">
            <div class="pt-good-bad__h">✅ {{ primer.good_task_label }}</div>
            <p>«{{ selectedCase.good_task }}»</p>
          </div>
          <div class="pt-good-bad__item pt-good-bad__item--bad">
            <div class="pt-good-bad__h">🚫 {{ primer.bad_task_label }}</div>
            <p>«{{ selectedCase.bad_task }}»</p>
          </div>
        </div>

        <div class="pt-questions">
          <div class="pt-questions__h">{{ $t('agileTraining.productThinking.decomposition.questionsTitle') }}</div>
          <ul>
            <li>{{ $t('agileTraining.productThinking.decomposition.q1') }}</li>
            <li>{{ $t('agileTraining.productThinking.decomposition.q2') }}</li>
            <li>{{ $t('agileTraining.productThinking.decomposition.q3') }}</li>
            <li>{{ $t('agileTraining.productThinking.decomposition.q4') }}</li>
            <li>{{ $t('agileTraining.productThinking.decomposition.q5') }}</li>
          </ul>
        </div>

        <div class="pt-hint" v-if="primer.start_small_hint">
          <strong>{{ $t('agileTraining.productThinking.decomposition.startSmallTitle') }}:</strong>
          {{ primer.start_small_hint }}
        </div>

        <TaskList
          :tasks="tasks"
          :placeholder="$t('agileTraining.productThinking.decomposition.placeholder')"
          :add-label="$t('agileTraining.productThinking.decomposition.addTask')"
          :remove-label="$t('agileTraining.productThinking.decomposition.removeTask')"
          :empty-hint="$t('agileTraining.productThinking.decomposition.emptyHint')"
          @update:tasks="onTasksUpdate"
        />
        <AiHelper
          ref="aiDecomp"
          :locale="locale"
          :mode="'decomposition'"
          :label="$t('agileTraining.productThinking.aiModeDecomposition')"
          :calls-remaining="aiRemaining"
          :initial-input="tasksAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.productThinking.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 9. Technique -->
      <div v-else-if="stage === 'technique'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.technique.title') }}</h2>
        <p class="pt-card__lead">👉 {{ $t('agileTraining.productThinking.technique.lead') }}</p>
        <div class="pt-tech-grid">
          <article
            class="pt-tech"
            :class="{ 'pt-tech--active': chosenTechnique === 'spidr' }"
            @click="selectTechnique('spidr')"
          >
            <div class="pt-tech__h">🧭 {{ content.techniques.spidr.title || $t('agileTraining.productThinking.technique.spidrTitle') }}</div>
            <div class="pt-tech__sub" v-if="content.techniques.spidr.subtitle">{{ content.techniques.spidr.subtitle }}</div>
            <ul>
              <li v-for="(it, i) in content.techniques.spidr.items" :key="i">
                <template v-if="isStepObject(it)">
                  <strong class="pt-tech__tag">{{ it.tag }}</strong> — {{ it.text }}
                </template>
                <template v-else>{{ it }}</template>
              </li>
            </ul>
          </article>
          <article
            class="pt-tech"
            :class="{ 'pt-tech--active': chosenTechnique === 'seven_dim' }"
            @click="selectTechnique('seven_dim')"
          >
            <div class="pt-tech__h">🔍 {{ content.techniques.seven_dim.title || $t('agileTraining.productThinking.technique.sevenDimTitle') }}</div>
            <div class="pt-tech__sub" v-if="content.techniques.seven_dim.subtitle">{{ content.techniques.seven_dim.subtitle }}</div>
            <ul>
              <li v-for="(it, i) in content.techniques.seven_dim.items" :key="i">
                <template v-if="isStepObject(it)">
                  <strong class="pt-tech__tag">{{ it.tag }}</strong> — {{ it.text }}
                </template>
                <template v-else>{{ it }}</template>
              </li>
            </ul>
          </article>
        </div>
        <button type="button" class="pt-btn pt-btn--ghost" @click="selectTechnique(null)">
          {{ $t('agileTraining.productThinking.technique.skip') }}
        </button>
      </div>

      <!-- 10. Improve -->
      <div v-else-if="stage === 'improve'" class="pt-card">
        <h2>{{ $t('agileTraining.productThinking.improve.title') }}</h2>
        <p class="pt-card__lead">👉 {{ $t('agileTraining.productThinking.improve.lead') }}</p>
        <p class="pt-explain">{{ $t('agileTraining.productThinking.improve.explain') }}</p>
        <button type="button" class="pt-btn pt-btn--ghost" @click="copyTasksToImproved">
          {{ $t('agileTraining.productThinking.improve.copyFromInitial') }}
        </button>
        <div class="pt-label pt-label--section">{{ $t('agileTraining.productThinking.improve.improvedTitle') }}</div>
        <TaskList
          :tasks="improvedTasks"
          :placeholder="$t('agileTraining.productThinking.decomposition.placeholder')"
          :add-label="$t('agileTraining.productThinking.decomposition.addTask')"
          :remove-label="$t('agileTraining.productThinking.decomposition.removeTask')"
          :empty-hint="$t('agileTraining.productThinking.decomposition.emptyHint')"
          @update:tasks="onImprovedUpdate"
        />
        <AiHelper
          ref="aiImprove"
          :locale="locale"
          :mode="'improve'"
          :label="$t('agileTraining.productThinking.aiModeImprove')"
          :calls-remaining="aiRemaining"
          :initial-input="improvedAsText || tasksAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.productThinking.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 11. Summary -->
      <div v-else-if="stage === 'summary'" class="pt-card pt-summary">
        <h2>{{ $t('agileTraining.productThinking.summary.title') }}</h2>
        <p class="pt-card__lead">👉 {{ $t('agileTraining.productThinking.summary.lead') }}</p>

        <div class="pt-summary__meta">
          <div><strong>{{ $t('agileTraining.productThinking.summary.participant') }}:</strong> {{ displayName || '—' }}</div>
          <div><strong>{{ $t('agileTraining.productThinking.summary.date') }}:</strong> {{ todayStr }}</div>
          <div v-if="selectedCase"><strong>{{ $t('agileTraining.productThinking.summary.caseTitle') }}:</strong> {{ selectedCase.title }}</div>
          <div v-if="selectedCase"><strong>{{ $t('agileTraining.productThinking.summary.epicLabel') }}:</strong> {{ selectedCase.epic_summary }}</div>
        </div>

        <div class="pt-summary__block">
          <div class="pt-summary__h">👤 {{ $t('agileTraining.productThinking.summary.userStoryTitle') }}</div>
          <p>{{ userStory || $t('agileTraining.productThinking.compare.empty') }}</p>
        </div>

        <div class="pt-summary__block">
          <div class="pt-summary__h">🎬 {{ $t('agileTraining.productThinking.summary.jobStoryTitle') }}</div>
          <p>{{ jobStory || $t('agileTraining.productThinking.compare.empty') }}</p>
        </div>

        <div class="pt-summary__block">
          <div class="pt-summary__h">🧩 {{ $t('agileTraining.productThinking.summary.tasksTitle') }}</div>
          <ul v-if="nonEmptyTasks.length">
            <li v-for="t in nonEmptyTasks" :key="t.id">{{ t.title }}<span v-if="t.note"> — {{ t.note }}</span></li>
          </ul>
          <p v-else class="pt-muted">{{ $t('agileTraining.productThinking.compare.empty') }}</p>
        </div>

        <div class="pt-summary__block" v-if="nonEmptyImprovedTasks.length">
          <div class="pt-summary__h">✨ {{ $t('agileTraining.productThinking.summary.improvedTitle') }}</div>
          <ul>
            <li v-for="t in nonEmptyImprovedTasks" :key="t.id">{{ t.title }}<span v-if="t.note"> — {{ t.note }}</span></li>
          </ul>
        </div>

        <div class="pt-summary__block">
          <div class="pt-summary__h">🛠 {{ $t('agileTraining.productThinking.summary.techniqueTitle') }}</div>
          <p>{{ techniqueLabel }}</p>
        </div>

        <div class="pt-important" data-html2canvas-ignore="true">
          <strong>{{ $t('agileTraining.productThinking.importantTitle') }}</strong>
          <ul>
            <li>{{ $t('agileTraining.productThinking.important1') }}</li>
            <li>{{ $t('agileTraining.productThinking.important2') }}</li>
          </ul>
        </div>

        <div class="pt-summary__actions" data-html2canvas-ignore="true">
          <button class="pt-btn pt-btn--primary" :disabled="pdfBusy" @click="downloadPdf">
            <span v-if="pdfBusy">{{ $t('agileTraining.productThinking.summary.downloadPdfLoading') }}</span>
            <span v-else>📄 {{ $t('agileTraining.productThinking.summary.downloadPdf') }}</span>
          </button>
          <div v-if="pdfError" class="pt-error">{{ pdfError }}</div>
        </div>
      </div>
    </section>

    <nav class="pt-play__nav" v-if="!loadError && !loading" data-html2canvas-ignore="true">
      <button
        type="button"
        class="pt-btn pt-btn--ghost"
        :disabled="stepIndex === 0"
        @click="goPrev"
      >← {{ $t('agileTraining.productThinking.back') }}</button>

      <span class="pt-play__ai-left" v-if="participantToken">
        🤖 {{ $t('agileTraining.productThinking.aiLimitLabel') }}: {{ aiRemaining }}
      </span>

      <button
        type="button"
        class="pt-btn pt-btn--primary"
        :disabled="stepIndex >= totalSteps - 1 || !canAdvance"
        @click="goNext"
      >{{ $t('agileTraining.productThinking.next') }} →</button>
    </nav>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport';
import AiHelper from '@/components/ProductThinking/AiHelper.vue';
import TaskList from '@/components/ProductThinking/TaskList.vue';

const STAGES = [
  'case_choice',
  'intro',
  'example',
  'user_story',
  'job_story',
  'compare',
  'epic',
  'decomposition_example',
  'decomposition',
  'technique',
  'improve',
  'summary',
];

const TOKEN_KEY_PREFIX = 'at_product_thinking_token_';
const NAME_KEY_PREFIX = 'at_product_thinking_name_';

function readStored(prefix, slug) {
  try {
    return localStorage.getItem(prefix + slug) || '';
  } catch (_) { return ''; }
}

function writeStored(prefix, slug, value) {
  try {
    if (value) localStorage.setItem(prefix + slug, value);
    else localStorage.removeItem(prefix + slug);
  } catch (_) { /* noop */ }
}

export default {
  name: 'AgileProductThinkingPlay',
  components: { AiHelper, TaskList },
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      loading: true,
      loadError: '',
      stage: 'case_choice',
      group: null,
      sessionInfo: this.prefetchedSession,
      content: { cases: [], primer: {}, techniques: { spidr: { items: [] }, seven_dim: { items: [] } } },
      caseKey: '',
      participantToken: '',
      displayName: '',
      joining: false,
      joinError: '',
      userStory: '',
      jobStory: '',
      chosenTechnique: null,
      tasks: [],
      improvedTasks: [],
      notes: { intro: '', compare: '' },
      aiCalls: 0,
      aiLimit: 15,
      savingState: '',
      saveTimer: null,
      pdfBusy: false,
      pdfError: '',
      locale: this.$i18n.locale || 'ru',
    };
  },
  computed: {
    stepIndex() {
      const idx = STAGES.indexOf(this.stage);
      return idx < 0 ? 0 : idx;
    },
    totalSteps() { return STAGES.length; },
    progressPct() { return Math.round(((this.stepIndex + 1) / this.totalSteps) * 100); },
    canAdvance() {
      if (this.stage === 'case_choice') return !!this.caseKey;
      if (this.stage === 'intro') return !!this.participantToken;
      return true;
    },
    availableCases() { return this.content && Array.isArray(this.content.cases) ? this.content.cases : []; },
    selectedCase() {
      if (!this.caseKey) return null;
      return this.availableCases.find(c => c.key === this.caseKey) || null;
    },
    primer() { return (this.content && this.content.primer) || {}; },
    decompositionVariants() {
      return this.selectedCase && Array.isArray(this.selectedCase.decomposition_examples)
        ? this.selectedCase.decomposition_examples
        : [];
    },
    aiRemaining() { return Math.max(0, this.aiLimit - (this.aiCalls || 0)); },
    nonEmptyTasks() {
      return this.tasks.filter(t => (t.title || '').trim());
    },
    nonEmptyImprovedTasks() {
      return this.improvedTasks.filter(t => (t.title || '').trim());
    },
    tasksAsText() {
      return this.nonEmptyTasks
        .map((t, i) => `${i + 1}. ${t.title}${t.note ? ' — ' + t.note : ''}`).join('\n');
    },
    improvedAsText() {
      return this.nonEmptyImprovedTasks
        .map((t, i) => `${i + 1}. ${t.title}${t.note ? ' — ' + t.note : ''}`).join('\n');
    },
    todayStr() {
      const d = new Date();
      return d.toLocaleDateString(this.locale === 'en' ? 'en-GB' : 'ru-RU');
    },
    techniqueLabel() {
      if (this.chosenTechnique === 'spidr') return this.$t('agileTraining.productThinking.summary.techniqueSpidr');
      if (this.chosenTechnique === 'seven_dim') return this.$t('agileTraining.productThinking.summary.techniqueSevenDim');
      return this.$t('agileTraining.productThinking.summary.techniqueNone');
    },
  },
  watch: {
    '$i18n.locale'(val) {
      if (val !== this.locale) {
        this.locale = val;
        this.loadContent();
      }
    },
  },
  async mounted() {
    this.participantToken = readStored(TOKEN_KEY_PREFIX, this.slug);
    this.displayName = readStored(NAME_KEY_PREFIX, this.slug);
    try {
      await this.loadState();
    } catch (e) {
      this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
    } finally {
      this.loading = false;
    }
  },
  beforeUnmount() { this.flushSave(); },
  methods: {
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* noop */ }
    },
    isStepObject(step) {
      return step !== null && typeof step === 'object' && (typeof step.tag === 'string' || typeof step.text === 'string');
    },
    hasEnvList(key) {
      const env = this.selectedCase && this.selectedCase.environment;
      const arr = env && env[key];
      return Array.isArray(arr) && arr.length > 0;
    },
    async loadState() {
      const params = { locale: this.locale };
      if (this.participantToken) params.participant_token = this.participantToken;
      const res = await axios.get(`/api/agile-training/product-thinking/g/${this.slug}/state`, { params });
      this.group = res.data.group;
      this.sessionInfo = res.data.session;
      this.content = res.data.content || this.content;
      if (res.data.ai_calls_limit) this.aiLimit = res.data.ai_calls_limit;
      if (res.data.effective_locale && res.data.effective_locale !== this.locale) {
        this.locale = res.data.effective_locale;
        this.$i18n.locale = this.locale;
      }
      const a = res.data.answer;
      if (a) {
        this.userStory = a.user_story || '';
        this.jobStory = a.job_story || '';
        this.chosenTechnique = a.chosen_technique || null;
        this.tasks = (a.tasks || []).map((t, i) => ({ id: t.id || `t${i+1}`, title: t.title || '', note: t.note || '' }));
        this.improvedTasks = (a.improved_tasks || []).map((t, i) => ({ id: t.id || `i${i+1}`, title: t.title || '', note: t.note || '' }));
        this.notes = Object.assign({ intro: '', compare: '' }, a.notes || {});
        this.aiCalls = a.ai_calls || 0;
        if (a.case_key) this.caseKey = a.case_key;
        if (a.stage && STAGES.includes(a.stage)) this.stage = a.stage;
      }
      if (!this.caseKey && this.stage !== 'case_choice') {
        this.stage = 'case_choice';
      }
    },
    async loadContent() {
      try {
        const res = await axios.get(`/api/agile-training/product-thinking/content`, { params: { locale: this.locale } });
        this.content = res.data;
      } catch (_) { /* keep old content */ }
    },
    async joinGroup() {
      this.joining = true;
      this.joinError = '';
      try {
        const body = { display_name: this.displayName || undefined };
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, body);
        this.participantToken = res.data.participant_token;
        writeStored(TOKEN_KEY_PREFIX, this.slug, this.participantToken);
        writeStored(NAME_KEY_PREFIX, this.slug, this.displayName);
        await this.persist({ immediate: true });
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.joining = false;
      }
    },
    goNext() {
      if (this.stepIndex >= STAGES.length - 1) return;
      this.stage = STAGES[this.stepIndex + 1];
      this.persist();
      this.scrollTop();
    },
    goPrev() {
      if (this.stepIndex <= 0) return;
      this.stage = STAGES[this.stepIndex - 1];
      this.persist();
      this.scrollTop();
    },
    scrollTop() {
      this.$nextTick(() => {
        try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) { /* noop */ }
      });
    },
    pickCase(key) {
      if (!key) return;
      this.caseKey = key;
      this.persist();
    },
    onTasksUpdate(next) { this.tasks = next; this.persist(); },
    onImprovedUpdate(next) { this.improvedTasks = next; this.persist(); },
    copyTasksToImproved() {
      this.improvedTasks = this.tasks.map((t, i) => ({ id: `i${i+1}`, title: t.title, note: t.note || '' }));
      this.persist();
    },
    selectTechnique(key) {
      this.chosenTechnique = key;
      this.persist();
    },
    persist(opts = {}) {
      if (!this.participantToken) return Promise.resolve();
      if (this.saveTimer) {
        clearTimeout(this.saveTimer);
        this.saveTimer = null;
      }
      if (opts.immediate) return this.doSave();
      return new Promise((resolve) => {
        this.saveTimer = setTimeout(async () => {
          await this.doSave();
          resolve();
        }, 400);
      });
    },
    flushSave() {
      if (this.saveTimer) {
        clearTimeout(this.saveTimer);
        this.saveTimer = null;
        this.doSave();
      }
    },
    async doSave() {
      if (!this.participantToken) return;
      this.savingState = 'saving';
      try {
        await axios.post(`/api/agile-training/product-thinking/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          stage: this.stage,
          case_key: this.caseKey || null,
          user_story: this.userStory,
          job_story: this.jobStory,
          chosen_technique: this.chosenTechnique,
          tasks: this.tasks
            .filter(t => (t.title || '').trim())
            .map(t => ({ title: (t.title || '').trim(), note: (t.note || '').trim() })),
          improved_tasks: this.improvedTasks
            .filter(t => (t.title || '').trim())
            .map(t => ({ title: (t.title || '').trim(), note: (t.note || '').trim() })),
          notes: this.notes,
        });
        this.savingState = 'saved';
        setTimeout(() => { if (this.savingState === 'saved') this.savingState = ''; }, 1200);
      } catch (e) {
        this.savingState = '';
      }
    },
    async askAi({ mode, input, resolve }) {
      if (!this.participantToken) {
        resolve({ error: this.$t('agileTraining.productThinking.needJoinHint') });
        return;
      }
      try {
        const res = await axios.post(`/api/agile-training/product-thinking/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken,
          mode,
          user_input: input,
          locale: this.locale,
        });
        this.aiCalls = this.aiLimit - (res.data.ai_calls_remaining || 0);
        resolve({ reply: res.data.reply || '', remaining: res.data.ai_calls_remaining });
      } catch (e) {
        const d = e && e.response && e.response.data;
        if (d && d.error === 'ai_limit_exceeded') {
          this.aiCalls = this.aiLimit;
          resolve({ error: this.$t('agileTraining.productThinking.aiHelperLimit') });
          return;
        }
        resolve({ error: this.$t('agileTraining.productThinking.aiHelperError') });
      }
    },
    async downloadPdf() {
      this.pdfError = '';
      this.pdfBusy = true;
      try {
        const name = `product-thinking_${this.displayName || 'participant'}_${this.slug}`;
        const res = await exportElementToPdf(this.$refs.pdfRoot, name);
        if (!res || !res.ok) {
          this.pdfError = this.$t('agileTraining.productThinking.summary.downloadPdfError');
        }
      } catch (_) {
        this.pdfError = this.$t('agileTraining.productThinking.summary.downloadPdfError');
      } finally {
        this.pdfBusy = false;
      }
    },
  },
};
</script>

<style scoped>
.pt-play {
  max-width: 880px;
  margin: 24px auto 80px;
  padding: 0 20px;
  color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
}
.pt-play__head { margin-bottom: 16px; }
.pt-play__lang {
  display: flex; justify-content: flex-end; gap: 4px;
}
.pt-play__lang button {
  border: 1px solid #e5e7eb; background: #fff; color: #475569;
  padding: 4px 10px; border-radius: 999px; font-size: 12px; cursor: pointer;
}
.pt-play__lang button.active { background: #7c3aed; color: #fff; border-color: #7c3aed; }
.pt-play__title { font-size: 22px; margin: 8px 0 6px; }
.pt-play__meta { color: #64748b; font-size: 13px; }
.pt-play__save { color: #7c3aed; }
.pt-play__save--ok { color: #059669; }
.pt-play__progressbar {
  margin-top: 10px; background: #ede9fe; height: 6px; border-radius: 999px; overflow: hidden;
}
.pt-play__progressbar-fill {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
  height: 100%;
  transition: width 0.25s ease;
}
.pt-play__error { padding: 20px; background: #fff1f2; color: #b91c1c; border-radius: 12px; }
.pt-play__loading { padding: 40px; text-align: center; color: #64748b; }

.pt-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 18px;
  padding: 22px 22px 24px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}
.pt-card h2 { margin: 0 0 10px; font-size: 20px; }
.pt-card__lead { color: #475569; margin: 4px 0 14px; line-height: 1.55; }

.pt-case {
  border: 1px dashed #c4b5fd; background: #faf5ff; border-radius: 14px;
  padding: 16px 18px; margin-bottom: 14px;
}
.pt-case__title { font-weight: 700; font-size: 16px; margin-bottom: 10px; color: #5b21b6; }
.pt-case__block { margin-bottom: 8px; }
.pt-case__h { font-weight: 600; color: #334155; margin-bottom: 4px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
.pt-case__block ul { margin: 0; padding-left: 20px; color: #475569; line-height: 1.6; }
.pt-case__goal { margin-top: 10px; color: #6d28d9; font-weight: 600; }
.pt-case__hint { margin-top: 6px; color: #475569; font-style: italic; }

.pt-start {
  margin-top: 18px; padding: 16px; background: #f8fafc;
  border-radius: 12px; border: 1px solid #e2e8f0;
}
.pt-label {
  display: block; font-weight: 600; font-size: 13px; color: #334155; margin-bottom: 6px;
}
.pt-label--section { margin-top: 16px; font-size: 14px; }
.pt-input, .pt-textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1;
  border-radius: 10px; font-size: 14px; font-family: inherit; color: #0f172a;
  background: #fff; box-sizing: border-box;
}
.pt-textarea { resize: vertical; min-height: 80px; line-height: 1.5; }
.pt-input:focus, .pt-textarea:focus { outline: none; border-color: #7c3aed; box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2); }

.pt-btn {
  border: none; border-radius: 10px; padding: 10px 18px;
  font-weight: 600; font-size: 14px; cursor: pointer;
  transition: all 0.15s ease; font-family: inherit;
}
.pt-btn--primary {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff;
}
.pt-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.pt-btn--ghost {
  background: #fff; border: 1px solid #cbd5e1; color: #475569;
}
.pt-btn--ghost:hover { border-color: #7c3aed; color: #7c3aed; }
.pt-btn--ghost:disabled { opacity: 0.5; cursor: not-allowed; }

.pt-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 12px 0; }
@media (max-width: 640px) { .pt-compare { grid-template-columns: 1fr; } }
.pt-compare__col {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 14px 16px;
}
.pt-compare__h { font-weight: 700; color: #5b21b6; margin-bottom: 6px; font-size: 14px; }
.pt-compare__quote { margin: 0; color: #1e293b; line-height: 1.5; font-style: italic; }
.pt-compare__quote--empty { color: #94a3b8; font-style: normal; }
.pt-compare__explain { margin-top: 10px; font-size: 13px; color: #64748b; }

.pt-note {
  background: #fef3c7; color: #92400e;
  border-radius: 10px; padding: 10px 14px; margin: 10px 0;
  line-height: 1.5; font-size: 14px;
}
.pt-explain { color: #475569; line-height: 1.6; }

.pt-questions {
  margin-top: 12px;
  background: #eff6ff; border-radius: 12px; padding: 12px 16px;
}
.pt-questions__h { font-weight: 700; color: #1e3a8a; margin-bottom: 4px; font-size: 13px; }
.pt-questions ul { margin: 4px 0 0; padding-left: 20px; color: #1e293b; line-height: 1.7; }

.pt-hint {
  margin: 12px 0; padding: 10px 14px;
  background: #ecfdf5; border-radius: 10px; color: #065f46; line-height: 1.5;
  border-left: 3px solid #10b981;
}

.pt-epic-card {
  margin: 14px 0;
  padding: 18px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #f59e0b;
  color: #7c2d12;
}
.pt-epic-card--compact { padding: 12px 16px; margin: 12px 0; }
.pt-epic-card__label {
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #92400e; margin-bottom: 4px;
}
.pt-epic-card__title {
  font-size: 20px; font-weight: 800; color: #7c2d12; line-height: 1.35;
}
.pt-epic-card--compact .pt-epic-card__title { font-size: 17px; }
.pt-epic-card__why {
  margin-top: 8px; font-size: 14px; line-height: 1.55; color: #7c2d12;
}
.pt-epic-summary {
  margin-top: 14px; padding: 12px 16px; background: #f8fafc;
  border-radius: 10px; color: #334155; line-height: 1.6;
  border: 1px solid #e2e8f0;
}
.pt-epic-summary__h {
  font-weight: 700; color: #1e293b; margin-bottom: 8px; font-size: 14px;
}
.pt-epic-summary div { margin-bottom: 6px; }
.pt-epic-summary div:last-child { margin-bottom: 0; }

.pt-case-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 14px 0;
}
@media (max-width: 640px) { .pt-case-grid { grid-template-columns: 1fr; } }
.pt-case-card {
  background: #fff; border: 2px solid #e5e7eb; border-radius: 14px;
  padding: 16px 18px; cursor: pointer; transition: all 0.15s ease;
  display: flex; flex-direction: column;
}
.pt-case-card:hover { border-color: #c4b5fd; transform: translateY(-1px); }
.pt-case-card--active { border-color: #7c3aed; background: #faf5ff; box-shadow: 0 4px 14px rgba(124, 58, 237, 0.15); }
.pt-case-card__emoji { font-size: 28px; margin-bottom: 6px; }
.pt-case-card__label {
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #6d28d9; margin-bottom: 4px;
}
.pt-case-card__title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 6px; line-height: 1.4; }
.pt-case-card__short { font-size: 13px; color: #64748b; line-height: 1.5; flex: 1; }
.pt-case-card__pick {
  margin-top: 12px; padding: 6px 12px; border-radius: 999px;
  background: #7c3aed; color: #fff; font-size: 12px; font-weight: 600;
  text-align: center;
}
.pt-case-card__pick--ghost { background: #f1f5f9; color: #475569; }

.pt-case__switch { margin-top: 12px; font-size: 13px; padding: 6px 12px; }

.pt-primer {
  margin: 14px 0; padding: 12px 16px;
  background: #eff6ff; border-left: 3px solid #3b82f6;
  border-radius: 10px; color: #1e3a8a;
}
.pt-primer__h { font-weight: 700; margin-bottom: 4px; font-size: 14px; }
.pt-primer p { margin: 0; line-height: 1.6; font-size: 14px; color: #1e293b; }

.pt-variants { display: grid; gap: 14px; margin: 14px 0; }
.pt-variant {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 14px 16px;
}
.pt-variant__h { font-weight: 700; color: #5b21b6; font-size: 15px; }
.pt-variant__sub { font-size: 13px; color: #64748b; margin: 4px 0 10px; line-height: 1.5; }

.pt-example-warn {
  margin: 14px 0; padding: 10px 14px;
  background: #fffbeb; border: 1px dashed #fcd34d; border-radius: 10px;
  color: #92400e;
}
.pt-example-warn__h { font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.pt-example-warn__p { margin: 0; color: #78350f; font-size: 14px; line-height: 1.5; }

.pt-env {
  margin: 16px 0;
  padding: 14px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
}
.pt-env__intro { font-weight: 700; color: #0f172a; margin-bottom: 10px; font-size: 14px; }
.pt-env__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 720px) { .pt-env__grid { grid-template-columns: 1fr; } }
.pt-env__block {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 10px 12px;
}
.pt-env__h {
  font-size: 12px; font-weight: 700; color: #334155;
  text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px;
}
.pt-env__block ul { margin: 0; padding-left: 18px; color: #475569; line-height: 1.55; font-size: 13px; }
.pt-env__block li { margin-bottom: 3px; }
.pt-env__hint { margin-top: 10px; font-size: 13px; color: #475569; font-style: italic; }

.pt-steps__tag {
  flex-shrink: 0;
  min-width: 110px;
  background: #ede9fe; color: #5b21b6;
  border-radius: 8px; padding: 4px 8px;
  font-size: 12px; font-weight: 700;
  text-align: center;
}
.pt-steps__text { color: #1e293b; line-height: 1.5; }
.pt-tech__sub { font-size: 12px; color: #64748b; margin-bottom: 6px; font-style: italic; }
.pt-tech__tag { color: #5b21b6; }

.pt-good-bad {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 14px 0;
}
@media (max-width: 640px) { .pt-good-bad { grid-template-columns: 1fr; } }
.pt-good-bad__item {
  padding: 12px 14px; border-radius: 12px; border: 1px solid;
}
.pt-good-bad__item--good { background: #ecfdf5; border-color: #6ee7b7; color: #065f46; }
.pt-good-bad__item--bad  { background: #fef2f2; border-color: #fca5a5; color: #991b1b; }
.pt-good-bad__h { font-weight: 700; font-size: 13px; margin-bottom: 6px; }
.pt-good-bad__item p { margin: 0; font-style: italic; line-height: 1.5; }

.pt-steps {
  list-style: none; padding: 0; margin: 16px 0 0;
  display: grid; gap: 10px;
}
.pt-steps li {
  display: flex; align-items: center; gap: 12px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  padding: 12px 14px; border-radius: 10px; color: #1e293b;
}
.pt-steps__num {
  width: 28px; height: 28px; border-radius: 50%;
  background: #7c3aed; color: #fff; display: inline-flex;
  align-items: center; justify-content: center; font-weight: 700;
  flex-shrink: 0;
}

.pt-tech-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 14px 0; }
@media (max-width: 640px) { .pt-tech-grid { grid-template-columns: 1fr; } }
.pt-tech {
  background: #fff; border: 2px solid #e5e7eb; border-radius: 14px;
  padding: 14px 16px; cursor: pointer; transition: all 0.15s ease;
}
.pt-tech:hover { border-color: #c4b5fd; }
.pt-tech--active { border-color: #7c3aed; background: #faf5ff; }
.pt-tech__h { font-weight: 700; color: #5b21b6; margin-bottom: 6px; }
.pt-tech ul { margin: 4px 0 0; padding-left: 20px; color: #475569; line-height: 1.6; font-size: 14px; }

.pt-play__nav {
  margin-top: 20px; display: flex; justify-content: space-between; align-items: center;
  gap: 10px;
}
.pt-play__ai-left { color: #64748b; font-size: 13px; }

.pt-summary__meta { display: grid; gap: 4px; color: #475569; margin-bottom: 14px; font-size: 14px; }
.pt-summary__block { margin-top: 14px; padding-top: 14px; border-top: 1px dashed #e2e8f0; }
.pt-summary__h { font-weight: 700; color: #5b21b6; margin-bottom: 6px; }
.pt-summary__block p { margin: 0; color: #1e293b; line-height: 1.6; }
.pt-summary__block ul { margin: 0; padding-left: 20px; color: #1e293b; line-height: 1.7; }
.pt-muted { color: #94a3b8; }

.pt-important {
  margin-top: 16px; padding: 12px 16px; background: #f1f5f9;
  border-radius: 10px; color: #334155; line-height: 1.6; font-size: 14px;
}
.pt-important ul { margin: 6px 0 0; padding-left: 20px; }

.pt-summary__actions {
  margin-top: 16px; display: flex; flex-direction: column; gap: 8px;
}
.pt-error { color: #b91c1c; font-size: 13px; }
</style>

<template>
  <div class="kb-play modern-ui" ref="pdfRoot">
    <header class="kb-play__head">
      <div class="kb-play__lang">
        <button type="button" :class="{ active: locale === 'ru' }" @click="switchLang('ru')">RU</button>
        <button type="button" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
      </div>
      <h1 class="kb-play__title">{{ $t('agileTraining.kanban.playTitle') }}</h1>
      <div class="kb-play__meta">
        <span class="kb-play__step">
          {{ $t('agileTraining.kanban.progress', { current: stepIndex + 1, total: totalSteps }) }}
        </span>
        <span class="kb-play__group" v-if="group">· {{ group.name }}</span>
        <span class="kb-play__save" v-if="savingState === 'saving'">· {{ $t('agileTraining.kanban.saving') }}</span>
        <span class="kb-play__save kb-play__save--ok" v-else-if="savingState === 'saved'">· {{ $t('agileTraining.kanban.saved') }}</span>
      </div>
      <div class="kb-play__progressbar">
        <div class="kb-play__progressbar-fill" :style="{ width: progressPct + '%' }" />
      </div>
    </header>

    <div v-if="loadError" class="kb-play__error">{{ loadError }}</div>

    <div v-else-if="loading" class="kb-play__loading">{{ $t('common.loading') }}…</div>

    <section v-else class="kb-play__stage">
      <!-- 0. Case choice -->
      <div v-if="stage === 'case_choice'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.caseChoice.title') }}</h2>
        <p class="kb-card__lead">{{ $t('agileTraining.kanban.caseChoice.lead') }}</p>
        <div class="kb-case-grid">
          <article
            v-for="c in availableCases"
            :key="c.key"
            class="kb-case-card"
            :class="{ 'kb-case-card--active': caseKey === c.key }"
            @click="pickCase(c.key)"
          >
            <div class="kb-case-card__emoji">{{ c.emoji }}</div>
            <div class="kb-case-card__label">{{ c.label }}</div>
            <div class="kb-case-card__title">{{ c.title }}</div>
            <div class="kb-case-card__short">{{ c.short }}</div>
            <div class="kb-case-card__pick" v-if="caseKey === c.key">
              ✓ {{ $t('agileTraining.kanban.caseChoice.picked') }}
            </div>
            <div class="kb-case-card__pick kb-case-card__pick--ghost" v-else>
              {{ $t('agileTraining.kanban.caseChoice.pickCta') }}
            </div>
          </article>
        </div>
      </div>

      <!-- 1. Intro -->
      <div v-else-if="stage === 'intro'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.intro.title') }}</h2>
        <p class="kb-card__lead">{{ $t('agileTraining.kanban.intro.lead') }}</p>
        <div class="kb-case" v-if="selectedCase">
          <div class="kb-case__title">{{ selectedCase.emoji }} {{ selectedCase.title }}</div>
          <div class="kb-case__block">
            <div class="kb-case__h">{{ $t('agileTraining.kanban.intro.contextTitle') }}</div>
            <ul>
              <li v-for="(line, i) in selectedCase.context" :key="i">{{ line }}</li>
            </ul>
          </div>
          <div class="kb-case__pain">🔥 {{ selectedCase.pain }}</div>
          <button
            type="button"
            class="kb-btn kb-btn--ghost kb-case__switch"
            @click="stage = 'case_choice'"
          >🔄 {{ $t('agileTraining.kanban.caseChoice.switch') }}</button>
        </div>
        <div class="kb-primer" v-if="primer.kanban_text">
          <div class="kb-primer__h">💡 {{ primer.kanban_title }}</div>
          <p>{{ primer.kanban_text }}</p>
        </div>
        <div v-if="!participantToken" class="kb-start">
          <label class="kb-label">{{ $t('agileTraining.kanban.nameAsk') }}</label>
          <input class="kb-input" type="text" v-model="displayName" :placeholder="$t('agileTraining.kanban.namePlaceholder')" />
          <button class="kb-btn kb-btn--primary" :disabled="joining" @click="joinGroup">
            {{ $t('agileTraining.kanban.start') }}
          </button>
          <div v-if="joinError" class="kb-error">{{ joinError }}</div>
        </div>
      </div>

      <!-- 2. Example -->
      <div v-else-if="stage === 'example'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.example.title') }}</h2>
        <p class="kb-card__lead">{{ $t('agileTraining.kanban.example.lead') }}</p>
        <div class="kb-example" v-if="selectedCase && selectedCase.example_static">
          <div class="kb-example__block">
            <div class="kb-example__h">👥 {{ $t('agileTraining.kanban.example.dissatisfactionInternal') }}</div>
            <p>«{{ selectedCase.example_static.dissatisfaction_internal }}»</p>
          </div>
          <div class="kb-example__block">
            <div class="kb-example__h">😟 {{ $t('agileTraining.kanban.example.dissatisfactionClient') }}</div>
            <p>«{{ selectedCase.example_static.dissatisfaction_client }}»</p>
          </div>
          <div class="kb-example__block">
            <div class="kb-example__h">📥 {{ $t('agileTraining.kanban.example.demandSample') }}</div>
            <ul class="kb-demand-sample">
              <li v-for="(d, i) in selectedCase.example_static.demand" :key="i">
                <strong>{{ d.type }}</strong><br/>
                <span>{{ d.source }} · {{ d.frequency }} · {{ d.expectations }}</span>
              </li>
            </ul>
          </div>
        </div>
        <p class="kb-explain">{{ $t('agileTraining.kanban.example.note') }}</p>
      </div>

      <!-- 3. Dissatisfaction -->
      <div v-else-if="stage === 'dissatisfaction'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.dissatisfaction.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.dissatisfaction.lead') }}</div>
        <div class="kb-chip-row" v-if="hints.dissatisfaction">
          <span class="kb-chip" v-for="(h, i) in hints.dissatisfaction" :key="i">{{ h }}</span>
        </div>

        <label class="kb-label">{{ $t('agileTraining.kanban.dissatisfaction.internalQ') }}</label>
        <textarea class="kb-textarea" rows="3" v-model="dissatisfaction.internal" @blur="persist" :placeholder="$t('agileTraining.kanban.dissatisfaction.internalPlaceholder')" />

        <label class="kb-label">{{ $t('agileTraining.kanban.dissatisfaction.clientQ') }}</label>
        <textarea class="kb-textarea" rows="3" v-model="dissatisfaction.client" @blur="persist" :placeholder="$t('agileTraining.kanban.dissatisfaction.clientPlaceholder')" />

        <AiHelper
          ref="aiDiss"
          :locale="locale"
          :mode="'dissatisfaction'"
          :label="$t('agileTraining.kanban.aiModeDissatisfaction')"
          :calls-remaining="aiRemaining"
          :initial-input="(dissatisfaction.internal || '') + '\n---\n' + (dissatisfaction.client || '')"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 4. Demand -->
      <div v-else-if="stage === 'demand'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.demand.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.demand.lead') }}</div>
        <div class="kb-table">
          <div class="kb-table__head">
            <div>{{ $t('agileTraining.kanban.demand.type') }}</div>
            <div>{{ $t('agileTraining.kanban.demand.source') }}</div>
            <div>{{ $t('agileTraining.kanban.demand.frequency') }}</div>
            <div>{{ $t('agileTraining.kanban.demand.expectations') }}</div>
            <div></div>
          </div>
          <div class="kb-table__row" v-for="(row, i) in demand" :key="row.id">
            <input class="kb-input" v-model="row.type" :placeholder="$t('agileTraining.kanban.demand.typePh')" @blur="persist"/>
            <input class="kb-input" v-model="row.source" :placeholder="$t('agileTraining.kanban.demand.sourcePh')" @blur="persist"/>
            <input class="kb-input" v-model="row.frequency" :placeholder="$t('agileTraining.kanban.demand.freqPh')" @blur="persist"/>
            <input class="kb-input" v-model="row.expectations" :placeholder="$t('agileTraining.kanban.demand.expPh')" @blur="persist"/>
            <button type="button" class="kb-icon-btn" @click="removeDemand(i)" :title="$t('agileTraining.kanban.remove')">×</button>
          </div>
        </div>
        <div class="kb-table__actions">
          <button type="button" class="kb-btn kb-btn--ghost" @click="addDemand">+ {{ $t('agileTraining.kanban.demand.add') }}</button>
          <button type="button" class="kb-btn kb-btn--ghost" v-if="selectedCase" @click="seedDemandFromExample">
            📋 {{ $t('agileTraining.kanban.demand.seed') }}
          </button>
        </div>
        <AiHelper
          ref="aiDemand"
          :locale="locale"
          :mode="'demand'"
          :label="$t('agileTraining.kanban.aiModeDemand')"
          :calls-remaining="aiRemaining"
          :initial-input="demandAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 5. Workflow -->
      <div v-else-if="stage === 'workflow'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.workflow.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.workflow.lead') }}</div>
        <div class="kb-primer">
          <div class="kb-primer__h">💡 {{ primer.flow_title }}</div>
          <p>{{ primer.flow_text }}</p>
        </div>
        <div class="kb-stages">
          <div class="kb-stage" v-for="(s, i) in workflow" :key="s.id">
            <span class="kb-stage__num">{{ i + 1 }}</span>
            <input class="kb-input kb-stage__input" v-model="s.name" :placeholder="$t('agileTraining.kanban.workflow.stagePh')" @blur="persist"/>
            <div class="kb-stage__move">
              <button type="button" class="kb-icon-btn" :disabled="i === 0" @click="moveStage(i, -1)">↑</button>
              <button type="button" class="kb-icon-btn" :disabled="i === workflow.length - 1" @click="moveStage(i, 1)">↓</button>
              <button type="button" class="kb-icon-btn" @click="removeStage(i)">×</button>
            </div>
          </div>
        </div>
        <div class="kb-table__actions">
          <button type="button" class="kb-btn kb-btn--ghost" @click="addStage">+ {{ $t('agileTraining.kanban.workflow.add') }}</button>
          <button type="button" class="kb-btn kb-btn--ghost" v-if="selectedCase" @click="seedWorkflowFromExample">
            📋 {{ $t('agileTraining.kanban.workflow.seed') }}
          </button>
        </div>
        <AiHelper
          ref="aiWorkflow"
          :locale="locale"
          :mode="'workflow'"
          :label="$t('agileTraining.kanban.aiModeWorkflow')"
          :calls-remaining="aiRemaining"
          :initial-input="workflowAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 6. Classes -->
      <div v-else-if="stage === 'classes'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.classes.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.classes.lead') }}</div>
        <div class="kb-primer">
          <div class="kb-primer__h">💡 {{ primer.class_title }}</div>
          <p>{{ primer.class_text }}</p>
        </div>
        <div class="kb-warn">⚠️ {{ primer.urgent_pitfall }}</div>
        <div class="kb-classes">
          <div class="kb-class" v-for="(c, i) in classes" :key="c.id">
            <input type="color" class="kb-class__color" v-model="c.color" @change="persist" />
            <input class="kb-input kb-class__name" v-model="c.name" :placeholder="$t('agileTraining.kanban.classes.namePh')" @blur="persist" />
            <input class="kb-input kb-class__crit" v-model="c.criteria" :placeholder="$t('agileTraining.kanban.classes.critPh')" @blur="persist" />
            <button type="button" class="kb-icon-btn" @click="removeClass(i)">×</button>
          </div>
        </div>
        <div class="kb-table__actions">
          <button type="button" class="kb-btn kb-btn--ghost" @click="addClass">+ {{ $t('agileTraining.kanban.classes.add') }}</button>
          <button type="button" class="kb-btn kb-btn--ghost" v-if="selectedCase" @click="seedClassesFromExample">
            📋 {{ $t('agileTraining.kanban.classes.seed') }}
          </button>
        </div>
        <AiHelper
          ref="aiClasses"
          :locale="locale"
          :mode="'classes'"
          :label="$t('agileTraining.kanban.aiModeClasses')"
          :calls-remaining="aiRemaining"
          :initial-input="classesAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 7. Policies -->
      <div v-else-if="stage === 'policies'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.policies.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.policies.lead') }}</div>
        <div class="kb-chip-row" v-if="hints.policies">
          <span class="kb-chip" v-for="(h, i) in hints.policies" :key="i" @click="addPolicy(h)">+ {{ h }}</span>
        </div>
        <div class="kb-policies">
          <div class="kb-policy" v-for="(p, i) in policies" :key="p.id">
            <textarea class="kb-textarea" rows="2" v-model="p.text" @blur="persist" :placeholder="$t('agileTraining.kanban.policies.ph')" />
            <button type="button" class="kb-icon-btn" @click="removePolicy(i)">×</button>
          </div>
        </div>
        <button type="button" class="kb-btn kb-btn--ghost" @click="addPolicy('')">+ {{ $t('agileTraining.kanban.policies.add') }}</button>
        <AiHelper
          ref="aiPol"
          :locale="locale"
          :mode="'policies'"
          :label="$t('agileTraining.kanban.aiModePolicies')"
          :calls-remaining="aiRemaining"
          :initial-input="policies.map(p=>'- '+p.text).join('\n')"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 8. Cadences -->
      <div v-else-if="stage === 'cadences'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.cadences.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.cadences.lead') }}</div>
        <div class="kb-cadence-group" v-if="content.cadences">
          <div class="kb-cadence">
            <div class="kb-cadence__h">🔁 {{ content.cadences.replenishment.title }}</div>
            <div class="kb-cadence__options">
              <button
                type="button"
                v-for="opt in content.cadences.replenishment.options"
                :key="opt.key"
                :class="['kb-opt', { 'kb-opt--active': cadences.replenishment === opt.key }]"
                @click="pickCadence('replenishment', opt.key)"
              >{{ opt.label }}</button>
            </div>
          </div>
          <div class="kb-cadence">
            <div class="kb-cadence__h">👀 {{ content.cadences.review.title }}</div>
            <div class="kb-cadence__options">
              <button
                type="button"
                v-for="opt in content.cadences.review.options"
                :key="opt.key"
                :class="['kb-opt', { 'kb-opt--active': cadences.review === opt.key }]"
                @click="pickCadence('review', opt.key)"
              >{{ opt.label }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 9. Board -->
      <div v-else-if="stage === 'board'" class="kb-card kb-card--wide">
        <h2>{{ $t('agileTraining.kanban.board.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.board.lead') }}</div>
        <div class="kb-primer">
          <div class="kb-primer__h">💡 {{ primer.wip_title }}</div>
          <p>{{ primer.wip_text }}</p>
        </div>
        <div class="kb-primer">
          <div class="kb-primer__h">🛣️ {{ primer.swimlane_title }}</div>
          <p>{{ primer.swimlane_text }}</p>
        </div>

        <KanbanBoard
          :workflow="workflow"
          :swimlanes="swimlanes"
          :classes="classes"
          :cards="cards"
          :column-limits="columnLimits"
          :editable="true"
          :t="boardT"
          @add-swimlane="addSwimlane"
          @rename-swimlane="renameSwimlane"
          @remove-swimlane="removeSwimlane"
          @seed-swimlanes="seedSwimlanes"
          @set-wip="setWip"
          @add-card="addCard"
          @update-card="updateCard"
          @remove-card="removeCard"
        />

        <AiHelper
          ref="aiBoard"
          :locale="locale"
          :mode="'board'"
          :label="$t('agileTraining.kanban.aiModeBoard')"
          :calls-remaining="aiRemaining"
          :initial-input="boardAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 10. Consequences -->
      <div v-else-if="stage === 'consequences'" class="kb-card">
        <h2>{{ $t('agileTraining.kanban.consequences.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.consequences.lead') }}</div>
        <button type="button" class="kb-btn kb-btn--ghost" @click="loadConsequences">
          🔄 {{ $t('agileTraining.kanban.consequences.refresh') }}
        </button>
        <div class="kb-consequences">
          <div
            class="kb-consequence"
            :class="'kb-consequence--' + c.severity"
            v-for="(c, i) in consequences"
            :key="i"
          >
            <div class="kb-consequence__h">
              <span v-if="c.severity === 'ok'">✅</span>
              <span v-else-if="c.severity === 'info'">💬</span>
              <span v-else-if="c.severity === 'warn'">⚠️</span>
              <span v-else>🚨</span>
              {{ c.title }}
            </div>
            <p>{{ c.hint }}</p>
          </div>
        </div>
      </div>

      <!-- 11. Improve -->
      <div v-else-if="stage === 'improve'" class="kb-card kb-card--wide">
        <h2>{{ $t('agileTraining.kanban.improve.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.improve.lead') }}</div>
        <p class="kb-explain">{{ $t('agileTraining.kanban.improve.explain') }}</p>

        <KanbanBoard
          :workflow="workflow"
          :swimlanes="swimlanes"
          :classes="classes"
          :cards="cards"
          :column-limits="columnLimits"
          :editable="true"
          :t="boardT"
          @add-swimlane="addSwimlane"
          @rename-swimlane="renameSwimlane"
          @remove-swimlane="removeSwimlane"
          @seed-swimlanes="seedSwimlanes"
          @set-wip="setWip"
          @add-card="addCard"
          @update-card="updateCard"
          @remove-card="removeCard"
        />

        <AiHelper
          ref="aiImprove"
          :locale="locale"
          :mode="'improve'"
          :label="$t('agileTraining.kanban.aiModeImprove')"
          :calls-remaining="aiRemaining"
          :initial-input="boardAsText"
          :disabled="!participantToken"
          :disabled-hint="$t('agileTraining.kanban.needJoinHint')"
          @ask="askAi"
        />
      </div>

      <!-- 12. Summary -->
      <div v-else-if="stage === 'summary'" class="kb-card kb-card--wide kb-summary">
        <h2>{{ $t('agileTraining.kanban.summary.title') }}</h2>
        <div class="kb-note">👉 {{ $t('agileTraining.kanban.summary.lead') }}</div>

        <div class="kb-summary__meta">
          <div><strong>{{ $t('agileTraining.kanban.summary.participant') }}:</strong> {{ displayName || '—' }}</div>
          <div><strong>{{ $t('agileTraining.kanban.summary.date') }}:</strong> {{ todayStr }}</div>
          <div v-if="selectedCase"><strong>{{ $t('agileTraining.kanban.summary.case') }}:</strong> {{ selectedCase.title }}</div>
        </div>

        <div class="kb-summary__block" v-if="dissatisfaction.internal || dissatisfaction.client">
          <div class="kb-summary__h">🔥 {{ $t('agileTraining.kanban.summary.dissatisfaction') }}</div>
          <div v-if="dissatisfaction.internal"><strong>{{ $t('agileTraining.kanban.dissatisfaction.internalQ') }}:</strong> {{ dissatisfaction.internal }}</div>
          <div v-if="dissatisfaction.client"><strong>{{ $t('agileTraining.kanban.dissatisfaction.clientQ') }}:</strong> {{ dissatisfaction.client }}</div>
        </div>

        <div class="kb-summary__block" v-if="demand.length">
          <div class="kb-summary__h">📥 {{ $t('agileTraining.kanban.summary.demand') }}</div>
          <ul>
            <li v-for="(d,i) in demand" :key="i">
              <strong>{{ d.type }}</strong>
              <span v-if="d.source"> — {{ d.source }}</span>
              <span v-if="d.frequency"> · {{ d.frequency }}</span>
              <span v-if="d.expectations"> · {{ d.expectations }}</span>
            </li>
          </ul>
        </div>

        <div class="kb-summary__block" v-if="classes.length">
          <div class="kb-summary__h">🏷️ {{ $t('agileTraining.kanban.summary.classes') }}</div>
          <ul>
            <li v-for="c in classes" :key="c.id">
              <span class="kb-class-pill" :style="{ background: c.color }">{{ c.name }}</span>
              <span v-if="c.criteria"> — {{ c.criteria }}</span>
            </li>
          </ul>
        </div>

        <div class="kb-summary__block" v-if="policies.length">
          <div class="kb-summary__h">📋 {{ $t('agileTraining.kanban.summary.policies') }}</div>
          <ul><li v-for="p in policies" :key="p.id">{{ p.text }}</li></ul>
        </div>

        <div class="kb-summary__block" v-if="cadences.replenishment || cadences.review">
          <div class="kb-summary__h">⏰ {{ $t('agileTraining.kanban.summary.cadences') }}</div>
          <div v-if="cadences.replenishment">🔁 {{ cadenceLabel('replenishment', cadences.replenishment) }}</div>
          <div v-if="cadences.review">👀 {{ cadenceLabel('review', cadences.review) }}</div>
        </div>

        <div class="kb-summary__block">
          <div class="kb-summary__h">🧩 {{ $t('agileTraining.kanban.summary.board') }}</div>
          <KanbanBoard
            :workflow="workflow"
            :swimlanes="swimlanes"
            :classes="classes"
            :cards="cards"
            :column-limits="columnLimits"
            :editable="false"
            :t="boardT"
          />
        </div>

        <div class="kb-important" data-html2canvas-ignore="true">
          <strong>{{ $t('agileTraining.kanban.importantTitle') }}</strong>
          <ul>
            <li>{{ $t('agileTraining.kanban.important1') }}</li>
            <li>{{ $t('agileTraining.kanban.important2') }}</li>
          </ul>
        </div>

        <div class="kb-summary__actions" data-html2canvas-ignore="true">
          <button class="kb-btn kb-btn--primary" :disabled="pdfBusy" @click="downloadPdf">
            <span v-if="pdfBusy">{{ $t('agileTraining.kanban.summary.downloadPdfLoading') }}</span>
            <span v-else>📄 {{ $t('agileTraining.kanban.summary.downloadPdf') }}</span>
          </button>
          <div v-if="pdfError" class="kb-error">{{ pdfError }}</div>
        </div>
      </div>
    </section>

    <nav class="kb-play__nav" v-if="!loadError && !loading" data-html2canvas-ignore="true">
      <button type="button" class="kb-btn kb-btn--ghost" :disabled="stepIndex === 0" @click="goPrev">← {{ $t('agileTraining.kanban.back') }}</button>
      <span class="kb-play__ai-left" v-if="participantToken">🤖 {{ $t('agileTraining.kanban.aiLimitLabel') }}: {{ aiRemaining }}</span>
      <button type="button" class="kb-btn kb-btn--primary" :disabled="stepIndex >= totalSteps - 1 || !canAdvance" @click="goNext">{{ $t('agileTraining.kanban.next') }} →</button>
    </nav>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport';
import AiHelper from '@/components/ProductThinking/AiHelper.vue';
import KanbanBoard from '@/components/Kanban/KanbanBoard.vue';

const STAGES = [
  'case_choice','intro','example','dissatisfaction','demand','workflow',
  'classes','policies','cadences','board','consequences','improve','summary',
];

const TOKEN_KEY_PREFIX = 'at_kanban_token_';
const NAME_KEY_PREFIX  = 'at_kanban_name_';

function readStored(prefix, slug) { try { return localStorage.getItem(prefix + slug) || ''; } catch (_) { return ''; } }
function writeStored(prefix, slug, value) {
  try { if (value) localStorage.setItem(prefix + slug, value); else localStorage.removeItem(prefix + slug); } catch (_) { /* noop */ }
}

function nextId(prefix, existing) {
  const used = new Set((existing || []).map(i => i.id));
  let n = existing.length + 1;
  while (used.has(prefix + n)) n++;
  return prefix + n;
}

export default {
  name: 'AgileKanbanPlay',
  components: { AiHelper, KanbanBoard },
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
      content: { cases: [], primer: {}, cadences: null, hints: {} },
      caseKey: '',
      participantToken: '',
      displayName: '',
      joining: false,
      joinError: '',
      dissatisfaction: { internal: '', client: '' },
      demand: [],
      workflow: [],
      classes: [],
      policies: [],
      cadences: { replenishment: '', review: '' },
      swimlanes: [],
      columnLimits: {},
      cards: [],
      consequences: [],
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
    availableCases() { return (this.content && Array.isArray(this.content.cases)) ? this.content.cases : []; },
    selectedCase() {
      if (!this.caseKey) return null;
      return this.availableCases.find(c => c.key === this.caseKey) || null;
    },
    primer() { return (this.content && this.content.primer) || {}; },
    hints() { return (this.content && this.content.hints) || {}; },
    aiRemaining() { return Math.max(0, this.aiLimit - (this.aiCalls || 0)); },
    todayStr() {
      const d = new Date();
      return d.toLocaleDateString(this.locale === 'en' ? 'en-GB' : 'ru-RU');
    },
    demandAsText() { return this.demand.map(d => `- ${d.type || ''} | ${d.source || ''} | ${d.frequency || ''} | ${d.expectations || ''}`).join('\n'); },
    workflowAsText() { return this.workflow.map((s, i) => `${i + 1}. ${s.name}`).join(' → '); },
    classesAsText() { return this.classes.map(c => `- ${c.name}: ${c.criteria || ''}`).join('\n'); },
    boardAsText() {
      const cols = this.workflow.map(c => `${c.name} (WIP ${this.columnLimits[c.id] || '—'})`).join(' | ');
      const lanes = this.swimlanes.map(l => l.name).join(' / ');
      return `Columns: ${cols}\nSwimlanes: ${lanes}\nCards: ${this.cards.length}`;
    },
    boardT() {
      return {
        wipLabel: this.$t('agileTraining.kanban.board.wipLabel'),
        wipPh: this.$t('agileTraining.kanban.board.wipPh'),
        addCard: this.$t('agileTraining.kanban.board.addCard'),
        addSwimlane: this.$t('agileTraining.kanban.board.addSwimlane'),
        seedSwimlanes: this.$t('agileTraining.kanban.board.seedSwimlanes'),
        removeSwimlane: this.$t('agileTraining.kanban.board.removeSwimlane'),
        renameSwimlane: this.$t('agileTraining.kanban.board.renameSwimlane'),
        cardTitle: this.$t('agileTraining.kanban.board.cardTitle'),
        cardClass: this.$t('agileTraining.kanban.board.cardClass'),
        cardNote: this.$t('agileTraining.kanban.board.cardNote'),
        cardSave: this.$t('agileTraining.kanban.board.cardSave'),
        cardCancel: this.$t('agileTraining.kanban.board.cardCancel'),
        cardDelete: this.$t('agileTraining.kanban.board.cardDelete'),
        noClass: this.$t('agileTraining.kanban.board.noClass'),
        emptyColumns: this.$t('agileTraining.kanban.board.emptyColumns'),
        emptyLanes: this.$t('agileTraining.kanban.board.emptyLanes'),
        overLimit: this.$t('agileTraining.kanban.board.overLimit'),
      };
    },
  },
  watch: {
    '$i18n.locale'(val) {
      if (val !== this.locale) { this.locale = val; this.loadContent(); }
    },
  },
  async mounted() {
    this.participantToken = readStored(TOKEN_KEY_PREFIX, this.slug);
    this.displayName = readStored(NAME_KEY_PREFIX, this.slug);
    try { await this.loadState(); }
    catch (e) { this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error'; }
    finally { this.loading = false; }
  },
  beforeUnmount() { this.flushSave(); },
  methods: {
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* noop */ }
    },
    async loadState() {
      const params = { locale: this.locale };
      if (this.participantToken) params.participant_token = this.participantToken;
      const res = await axios.get(`/api/agile-training/kanban/g/${this.slug}/state`, { params });
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
        this.caseKey = a.case_key || '';
        this.dissatisfaction = Object.assign({ internal: '', client: '' }, a.dissatisfaction || {});
        this.demand = (a.demand || []).slice();
        this.workflow = (a.workflow || []).slice();
        this.classes = (a.classes || []).slice();
        this.policies = (a.policies || []).slice();
        this.cadences = Object.assign({ replenishment: '', review: '' }, a.cadences || {});
        this.swimlanes = (a.swimlanes || []).slice();
        this.columnLimits = Object.assign({}, a.column_limits || {});
        this.cards = (a.cards || []).slice();
        this.aiCalls = a.ai_calls || 0;
        if (a.stage && STAGES.includes(a.stage)) this.stage = a.stage;
      }
      if (!this.caseKey && this.stage !== 'case_choice') this.stage = 'case_choice';
    },
    async loadContent() {
      try {
        const res = await axios.get(`/api/agile-training/kanban/content`, { params: { locale: this.locale } });
        this.content = res.data;
      } catch (_) { /* keep */ }
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
      if (this.stage === 'consequences') this.loadConsequences();
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
      this.$nextTick(() => { try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) { /* noop */ } });
    },
    pickCase(key) { if (key) { this.caseKey = key; this.persist(); } },

    // demand
    addDemand() { this.demand.push({ id: nextId('d', this.demand), type: '', source: '', frequency: '', expectations: '' }); this.persist(); },
    removeDemand(i) { this.demand.splice(i, 1); this.persist(); },
    seedDemandFromExample() {
      const ex = this.selectedCase && this.selectedCase.example_static && this.selectedCase.example_static.demand;
      if (!ex) return;
      ex.forEach(row => this.demand.push({ id: nextId('d', this.demand), ...row }));
      this.persist();
    },
    // workflow
    addStage() { this.workflow.push({ id: nextId('s', this.workflow), name: '' }); this.persist(); },
    removeStage(i) {
      const id = this.workflow[i] && this.workflow[i].id;
      this.workflow.splice(i, 1);
      if (id) {
        delete this.columnLimits[id];
        this.cards = this.cards.filter(c => c.column_id !== id);
      }
      this.persist();
    },
    moveStage(i, dir) {
      const j = i + dir;
      if (j < 0 || j >= this.workflow.length) return;
      const arr = this.workflow.slice();
      const [moved] = arr.splice(i, 1);
      arr.splice(j, 0, moved);
      this.workflow = arr;
      this.persist();
    },
    seedWorkflowFromExample() {
      const ex = this.selectedCase && this.selectedCase.suggested_workflow;
      if (!ex) return;
      ex.forEach(name => this.workflow.push({ id: nextId('s', this.workflow), name }));
      this.persist();
    },
    // classes
    addClass() { this.classes.push({ id: nextId('c', this.classes), name: '', color: '#0ea5e9', criteria: '' }); this.persist(); },
    removeClass(i) {
      const id = this.classes[i] && this.classes[i].id;
      this.classes.splice(i, 1);
      if (id) this.cards = this.cards.map(c => c.class_id === id ? { ...c, class_id: '' } : c);
      this.persist();
    },
    seedClassesFromExample() {
      const ex = this.selectedCase && this.selectedCase.suggested_classes;
      if (!ex) return;
      ex.forEach(c => this.classes.push({ id: nextId('c', this.classes), ...c }));
      this.persist();
    },
    // policies
    addPolicy(text) { this.policies.push({ id: 'p' + (this.policies.length + 1), text: text || '' }); this.persist(); },
    removePolicy(i) { this.policies.splice(i, 1); this.persist(); },
    // cadences
    pickCadence(kind, key) { this.cadences[kind] = key; this.persist(); },
    cadenceLabel(kind, key) {
      const opts = (this.content.cadences && this.content.cadences[kind] && this.content.cadences[kind].options) || [];
      const match = opts.find(o => o.key === key);
      return match ? match.label : key;
    },
    // board
    setWip(columnId, value) {
      const v = parseInt(value, 10);
      if (!columnId) return;
      if (!isFinite(v) || v <= 0) {
        delete this.columnLimits[columnId];
      } else {
        this.columnLimits[columnId] = Math.min(99, v);
      }
      this.columnLimits = Object.assign({}, this.columnLimits);
      this.persist();
    },
    addSwimlane(name) {
      if (this.swimlanes.length >= 6) return;
      const lane = { id: nextId('l', this.swimlanes), name: name || ('Swimlane ' + (this.swimlanes.length + 1)) };
      this.swimlanes.push(lane);
      this.persist();
    },
    renameSwimlane(id, name) {
      const l = this.swimlanes.find(x => x.id === id);
      if (l) { l.name = name; this.persist(); }
    },
    removeSwimlane(id) {
      this.swimlanes = this.swimlanes.filter(l => l.id !== id);
      this.cards = this.cards.filter(c => c.lane_id !== id);
      this.persist();
    },
    seedSwimlanes() {
      const ex = this.selectedCase && this.selectedCase.suggested_swimlanes;
      if (!ex) return;
      ex.forEach(l => {
        if (this.swimlanes.length < 6) this.swimlanes.push({ id: nextId('l', this.swimlanes), name: l.name });
      });
      this.persist();
    },
    addCard(payload) {
      if (this.cards.length >= 60) return;
      const id = 'k' + Date.now().toString(36) + Math.floor(Math.random() * 1000);
      this.cards.push({
        id,
        title: payload.title || '',
        column_id: payload.column_id || '',
        lane_id: payload.lane_id || '',
        class_id: payload.class_id || '',
        note: payload.note || '',
      });
      this.persist();
    },
    updateCard(id, patch) {
      const idx = this.cards.findIndex(c => c.id === id);
      if (idx < 0) return;
      this.cards.splice(idx, 1, Object.assign({}, this.cards[idx], patch));
      this.persist();
    },
    removeCard(id) {
      this.cards = this.cards.filter(c => c.id !== id);
      this.persist();
    },

    async loadConsequences() {
      if (!this.participantToken) { this.consequences = []; return; }
      await this.persist({ immediate: true });
      try {
        const res = await axios.get(`/api/agile-training/kanban/g/${this.slug}/consequences`, { params: {
          participant_token: this.participantToken, locale: this.locale,
        }});
        this.consequences = res.data.consequences || [];
      } catch (_) { this.consequences = []; }
    },

    persist(opts = {}) {
      if (!this.participantToken) return Promise.resolve();
      if (this.saveTimer) { clearTimeout(this.saveTimer); this.saveTimer = null; }
      if (opts.immediate) return this.doSave();
      return new Promise((resolve) => {
        this.saveTimer = setTimeout(async () => { await this.doSave(); resolve(); }, 400);
      });
    },
    flushSave() { if (this.saveTimer) { clearTimeout(this.saveTimer); this.saveTimer = null; this.doSave(); } },
    async doSave() {
      if (!this.participantToken) return;
      this.savingState = 'saving';
      try {
        await axios.post(`/api/agile-training/kanban/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          stage: this.stage,
          case_key: this.caseKey || null,
          dissatisfaction: this.dissatisfaction,
          demand: this.demand,
          workflow: this.workflow,
          classes: this.classes,
          policies: this.policies,
          cadences: this.cadences,
          swimlanes: this.swimlanes,
          column_limits: this.columnLimits,
          cards: this.cards,
        });
        this.savingState = 'saved';
        setTimeout(() => { if (this.savingState === 'saved') this.savingState = ''; }, 1200);
      } catch (_) { this.savingState = ''; }
    },
    async askAi({ mode, input, resolve }) {
      if (!this.participantToken) { resolve({ error: this.$t('agileTraining.kanban.needJoinHint') }); return; }
      try {
        const res = await axios.post(`/api/agile-training/kanban/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken,
          mode, user_input: input, locale: this.locale,
        });
        this.aiCalls = this.aiLimit - (res.data.ai_calls_remaining || 0);
        resolve({ reply: res.data.reply || '', remaining: res.data.ai_calls_remaining });
      } catch (e) {
        const d = e && e.response && e.response.data;
        if (d && d.error === 'ai_limit_exceeded') {
          this.aiCalls = this.aiLimit;
          resolve({ error: this.$t('agileTraining.kanban.aiHelperLimit') });
          return;
        }
        resolve({ error: this.$t('agileTraining.kanban.aiHelperError') });
      }
    },
    async downloadPdf() {
      this.pdfError = '';
      this.pdfBusy = true;
      try {
        const name = `kanban_${this.displayName || 'participant'}_${this.slug}`;
        const res = await exportElementToPdf(this.$refs.pdfRoot, name);
        if (!res || !res.ok) this.pdfError = this.$t('agileTraining.kanban.summary.downloadPdfError');
      } catch (_) {
        this.pdfError = this.$t('agileTraining.kanban.summary.downloadPdfError');
      } finally {
        this.pdfBusy = false;
      }
    },
  },
};
</script>

<style scoped>
.kb-play {
  max-width: 1040px; margin: 24px auto 80px; padding: 0 20px; color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
}
.kb-play__head { margin-bottom: 16px; }
.kb-play__lang { display: flex; justify-content: flex-end; gap: 4px; }
.kb-play__lang button {
  border: 1px solid #e5e7eb; background: #fff; color: #475569;
  padding: 4px 10px; border-radius: 999px; font-size: 12px; cursor: pointer;
}
.kb-play__lang button.active { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }
.kb-play__title { font-size: 22px; margin: 8px 0 6px; }
.kb-play__meta { color: #64748b; font-size: 13px; }
.kb-play__save { color: #0ea5e9; }
.kb-play__save--ok { color: #059669; }
.kb-play__progressbar { margin-top: 10px; background: #e0f2fe; height: 6px; border-radius: 999px; overflow: hidden; }
.kb-play__progressbar-fill { background: linear-gradient(135deg, #38bdf8, #0284c7); height: 100%; transition: width 0.25s ease; }
.kb-play__error { padding: 20px; background: #fff1f2; color: #b91c1c; border-radius: 12px; }
.kb-play__loading { padding: 40px; text-align: center; color: #64748b; }

.kb-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 18px;
  padding: 22px 22px 24px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}
.kb-card--wide { padding: 18px 16px 20px; }
.kb-card h2 { margin: 0 0 10px; font-size: 20px; }
.kb-card__lead { color: #475569; margin: 4px 0 14px; line-height: 1.55; }

.kb-case {
  border: 1px dashed #7dd3fc; background: #f0f9ff; border-radius: 14px;
  padding: 16px 18px; margin-bottom: 14px;
}
.kb-case__title { font-weight: 700; font-size: 16px; margin-bottom: 10px; color: #0c4a6e; }
.kb-case__block { margin-bottom: 8px; }
.kb-case__h { font-weight: 600; color: #334155; margin-bottom: 4px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
.kb-case__block ul { margin: 0; padding-left: 20px; color: #475569; line-height: 1.6; }
.kb-case__pain { margin-top: 10px; padding: 8px 12px; background: #fef2f2; color: #991b1b; border-radius: 8px; font-weight: 600; }
.kb-case__switch { margin-top: 12px; font-size: 13px; padding: 6px 12px; }

.kb-start { margin-top: 18px; padding: 16px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; }
.kb-label { display: block; font-weight: 600; font-size: 13px; color: #334155; margin: 10px 0 6px; }
.kb-input, .kb-textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1;
  border-radius: 10px; font-size: 14px; font-family: inherit; color: #0f172a;
  background: #fff; box-sizing: border-box;
}
.kb-textarea { resize: vertical; min-height: 80px; line-height: 1.5; }
.kb-input:focus, .kb-textarea:focus { outline: none; border-color: #0ea5e9; box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2); }

.kb-btn { border: none; border-radius: 10px; padding: 10px 18px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all 0.15s ease; font-family: inherit; }
.kb-btn--primary { background: linear-gradient(135deg, #38bdf8, #0284c7); color: #fff; }
.kb-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.kb-btn--ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; }
.kb-btn--ghost:hover { border-color: #0ea5e9; color: #0ea5e9; }
.kb-btn--ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.kb-icon-btn { border: 1px solid #e2e8f0; background: #fff; color: #64748b; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; }
.kb-icon-btn:hover { border-color: #ef4444; color: #ef4444; }
.kb-icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.kb-case-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 14px 0; }
@media (max-width: 640px) { .kb-case-grid { grid-template-columns: 1fr; } }
.kb-case-card {
  background: #fff; border: 2px solid #e5e7eb; border-radius: 14px;
  padding: 16px 18px; cursor: pointer; transition: all 0.15s ease;
  display: flex; flex-direction: column;
}
.kb-case-card:hover { border-color: #7dd3fc; transform: translateY(-1px); }
.kb-case-card--active { border-color: #0ea5e9; background: #f0f9ff; box-shadow: 0 4px 14px rgba(14, 165, 233, 0.15); }
.kb-case-card__emoji { font-size: 28px; margin-bottom: 6px; }
.kb-case-card__label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0284c7; margin-bottom: 4px; }
.kb-case-card__title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 6px; line-height: 1.4; }
.kb-case-card__short { font-size: 13px; color: #64748b; line-height: 1.5; flex: 1; }
.kb-case-card__pick { margin-top: 12px; padding: 6px 12px; border-radius: 999px; background: #0ea5e9; color: #fff; font-size: 12px; font-weight: 600; text-align: center; }
.kb-case-card__pick--ghost { background: #f1f5f9; color: #475569; }

.kb-primer {
  margin: 12px 0; padding: 12px 16px;
  background: #eff6ff; border-left: 3px solid #3b82f6;
  border-radius: 10px;
}
.kb-primer__h { font-weight: 700; margin-bottom: 4px; font-size: 14px; color: #1e3a8a; }
.kb-primer p { margin: 0; line-height: 1.6; font-size: 14px; color: #1e293b; }

.kb-warn { margin: 10px 0; padding: 10px 14px; background: #fef3c7; color: #92400e; border-radius: 10px; line-height: 1.5; font-size: 14px; }
.kb-note { background: #fef3c7; color: #92400e; border-radius: 10px; padding: 10px 14px; margin: 10px 0; line-height: 1.5; font-size: 14px; }
.kb-explain { color: #475569; line-height: 1.6; }
.kb-error { color: #b91c1c; font-size: 13px; }

.kb-example { display: grid; gap: 10px; margin: 12px 0; }
.kb-example__block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; }
.kb-example__h { font-weight: 700; color: #0c4a6e; margin-bottom: 6px; font-size: 14px; }
.kb-example__block p { margin: 0; color: #1e293b; font-style: italic; line-height: 1.5; }
.kb-demand-sample { list-style: none; padding: 0; margin: 4px 0 0; display: grid; gap: 6px; }
.kb-demand-sample li { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; font-size: 13px; color: #334155; }

.kb-chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 14px; }
.kb-chip {
  background: #e0f2fe; color: #0369a1; border-radius: 999px;
  padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer;
}
.kb-chip:hover { background: #bae6fd; }

.kb-table { display: grid; gap: 6px; margin: 10px 0; }
.kb-table__head, .kb-table__row { display: grid; grid-template-columns: 1.3fr 1fr 1fr 1.4fr 32px; gap: 6px; }
.kb-table__head { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 0 4px; }
.kb-table__actions { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
@media (max-width: 700px) {
  .kb-table__head { display: none; }
  .kb-table__row { grid-template-columns: 1fr 32px; grid-template-areas: "t x" "s x" "f x" "e x"; }
  .kb-table__row > :nth-child(1) { grid-area: t; }
  .kb-table__row > :nth-child(2) { grid-area: s; }
  .kb-table__row > :nth-child(3) { grid-area: f; }
  .kb-table__row > :nth-child(4) { grid-area: e; }
  .kb-table__row > :nth-child(5) { grid-area: x; }
}

.kb-stages { display: grid; gap: 8px; margin: 10px 0; }
.kb-stage { display: flex; align-items: center; gap: 8px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px 10px; border-radius: 10px; }
.kb-stage__num { width: 26px; height: 26px; border-radius: 50%; background: #0ea5e9; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; flex-shrink: 0; }
.kb-stage__input { flex: 1; }
.kb-stage__move { display: flex; gap: 4px; }

.kb-classes { display: grid; gap: 8px; margin: 10px 0; }
.kb-class { display: grid; grid-template-columns: 40px 1fr 2fr 32px; gap: 8px; align-items: center; background: #f8fafc; border: 1px solid #e2e8f0; padding: 6px 10px; border-radius: 10px; }
.kb-class__color { width: 36px; height: 36px; padding: 0; border: 1px solid #cbd5e1; border-radius: 8px; cursor: pointer; background: #fff; }
@media (max-width: 640px) { .kb-class { grid-template-columns: 40px 1fr 32px; grid-template-areas: "c n x" "c k x"; } .kb-class__name { grid-area: n; } .kb-class__crit { grid-area: k; } }

.kb-policies { display: grid; gap: 8px; margin: 10px 0; }
.kb-policy { display: grid; grid-template-columns: 1fr 32px; gap: 8px; align-items: start; }

.kb-cadence-group { display: grid; gap: 16px; margin-top: 10px; }
.kb-cadence { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; }
.kb-cadence__h { font-weight: 700; color: #0c4a6e; margin-bottom: 8px; }
.kb-cadence__options { display: flex; flex-wrap: wrap; gap: 6px; }
.kb-opt { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 6px 12px; border-radius: 999px; font-size: 13px; cursor: pointer; }
.kb-opt:hover { border-color: #0ea5e9; color: #0ea5e9; }
.kb-opt--active { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }

.kb-consequences { display: grid; gap: 8px; margin-top: 14px; }
.kb-consequence { padding: 12px 14px; border-radius: 10px; border: 1px solid; line-height: 1.5; }
.kb-consequence__h { font-weight: 700; margin-bottom: 4px; }
.kb-consequence p { margin: 0; font-size: 14px; }
.kb-consequence--ok { background: #ecfdf5; border-color: #6ee7b7; color: #065f46; }
.kb-consequence--info { background: #eff6ff; border-color: #bfdbfe; color: #1e3a8a; }
.kb-consequence--warn { background: #fef3c7; border-color: #fcd34d; color: #78350f; }
.kb-consequence--danger { background: #fef2f2; border-color: #fca5a5; color: #991b1b; }

.kb-play__nav { margin-top: 20px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.kb-play__ai-left { color: #64748b; font-size: 13px; }

.kb-summary__meta { display: grid; gap: 4px; color: #475569; margin-bottom: 14px; font-size: 14px; }
.kb-summary__block { margin-top: 14px; padding-top: 14px; border-top: 1px dashed #e2e8f0; }
.kb-summary__h { font-weight: 700; color: #0c4a6e; margin-bottom: 6px; }
.kb-summary__block ul { margin: 0; padding-left: 20px; color: #1e293b; line-height: 1.7; }
.kb-class-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; color: #fff; font-size: 12px; font-weight: 700; margin-right: 4px; }
.kb-important { margin-top: 16px; padding: 12px 16px; background: #f1f5f9; border-radius: 10px; color: #334155; line-height: 1.6; font-size: 14px; }
.kb-important ul { margin: 6px 0 0; padding-left: 20px; }
.kb-summary__actions { margin-top: 16px; display: flex; flex-direction: column; gap: 8px; }
</style>

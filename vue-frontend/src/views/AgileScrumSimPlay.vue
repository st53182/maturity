<template>
  <div class="sp modern-ui" v-if="!loading">
    <header class="sp__head">
      <div class="sp__head-left">
        <h1>🧩 {{ $t('agileTraining.scrumSim.title') }}</h1>
        <p class="sp__sub" v-if="group">
          <span class="sp__sub-grp">{{ group.name }}</span>
          · {{ $t('agileTraining.scrumSim.teamSize', { n: participantsCount }) }}
        </p>
      </div>
      <div class="sp__head-right">
        <span class="sp__phase-chip" :class="'sp__phase-chip--' + phaseClass">{{ phaseLabel }}</span>
        <button class="sp__lang" :class="{ active: locale === 'ru' }" @click="switchLang('ru')">RU</button>
        <button class="sp__lang" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
      </div>
    </header>

    <!-- Error bar -->
    <div v-if="loadError" class="sp__err">{{ loadError }}</div>

    <!-- LOBBY: join form -->
    <section v-if="!participantToken" class="sp__join">
      <h2>{{ $t('agileTraining.scrumSim.joinTitle') }}</h2>
      <p class="sp__story-line">{{ $t('agileTraining.scrumSim.joinIntro') }}</p>
      <div class="sp__join-row">
        <input v-model="displayName" class="sp__input" maxlength="60" :placeholder="$t('agileTraining.scrumSim.yourName')" />
        <button class="sp__btn sp__btn--primary" :disabled="joining || !displayName.trim()" @click="joinGroup">
          {{ joining ? '…' : $t('agileTraining.scrumSim.join') }}
        </button>
      </div>
      <div class="sp__err" v-if="joinError">{{ joinError }}</div>
    </section>

    <!-- LOBBY + PLANNING + DAYS + REVIEW + RETRO + SUMMARY -->
    <template v-else-if="state">
      <!-- Team / role bar -->
      <section class="sp__team">
        <div class="sp__team-members">
          <div
            v-for="pmember in participantList"
            :key="pmember.token"
            class="sp__member"
            :class="{ 'sp__member--me': pmember.token === participantToken }"
          >
            <span class="sp__member-name">{{ pmember.name || '…' }}</span>
            <span v-if="pmember.role" class="sp__member-role">{{ roleLabel(pmember.role) }}</span>
          </div>
        </div>
        <div class="sp__team-my-role">
          <label>{{ $t('agileTraining.scrumSim.myRole') }}:</label>
          <select class="sp__select" :value="myRole" @change="changeRole($event.target.value)">
            <option value="">{{ $t('agileTraining.scrumSim.noRole') }}</option>
            <option v-for="r in content.roles || []" :key="r.key" :value="r.key">{{ r.title }}</option>
          </select>
          <button v-if="myRoleInfo" class="sp__btn sp__btn--ghost sp__btn--tiny" @click="showRoleDesc = !showRoleDesc">
            {{ showRoleDesc ? $t('agileTraining.scrumSim.hide') : $t('agileTraining.scrumSim.whatIsThis') }}
          </button>
        </div>
      </section>
      <div v-if="showRoleDesc && myRoleInfo" class="sp__role-desc">
        <strong>{{ myRoleInfo.title }}.</strong> {{ myRoleInfo.desc }}
      </div>

      <!-- Always-visible Scrum board (shrunk when not main focus) -->
      <section class="sp__board-wrap">
        <div class="sp__board-head">
          <h3>{{ $t('agileTraining.scrumSim.boardTitle') }}</h3>
          <span v-if="state.sprint_goal" class="sp__goal-chip">🎯 {{ state.sprint_goal }}</span>
        </div>
        <ScrumBoard
          :tasks="state.tasks"
          :columns="boardColumns"
          :selectable="boardSelectable"
          :selected-keys="selectedTaskKeys"
          :pulse-keys="pulseKeys"
          :highlight-column="highlightColumn"
          :allocation="pendingAllocation"
          :compact="compactBoard"
          :planning-mode="phase === 'planning'"
          @task-click="onBoardTaskClick"
        />
      </section>

      <!-- PHASE: lobby (before planning) -->
      <section v-if="phase === 'lobby'" class="sp__card">
        <h3>{{ content.context.title }}</h3>
        <ul class="sp__bullets">
          <li v-for="(line, i) in content.context.story" :key="i">{{ line }}</li>
        </ul>
        <div class="sp__actions">
          <button class="sp__btn sp__btn--primary" @click="startPlanning">
            {{ $t('agileTraining.scrumSim.startPlanning') }}
          </button>
        </div>
      </section>

      <!-- PHASE: planning -->
      <section v-if="phase === 'planning'" class="sp__card">
        <h3>{{ $t('agileTraining.scrumSim.planningTitle') }}</h3>
        <div v-if="flashMessage" class="sp__flash sp__flash--chain">
          🔗 {{ flashMessage }}
        </div>
        <p class="sp__hint sp__planning-depshint">
          💡 {{ $t('agileTraining.scrumSim.planningDepsHint') }}
        </p>
        <p class="sp__hint sp__planning-depshint">
          🎲 {{ $t('agileTraining.scrumSim.planningEventsHint') }}
        </p>
        <p class="sp__hint">{{ content.context.sprint_goal_hint }}</p>
        <label class="sp__label">{{ $t('agileTraining.scrumSim.sprintGoal') }}</label>
        <textarea
          v-model="sprintGoalDraft"
          class="sp__textarea"
          rows="2"
          maxlength="240"
          :placeholder="$t('agileTraining.scrumSim.sprintGoalPh')"
          @blur="saveSprintGoal"
        ></textarea>
        <div class="sp__planning-help">
          <div>
            <strong>{{ $t('agileTraining.scrumSim.planningHow') }}</strong>
            <ul class="sp__bullets">
              <li>{{ $t('agileTraining.scrumSim.planningBullet1') }}</li>
              <li>{{ $t('agileTraining.scrumSim.planningBullet2') }}</li>
              <li>{{ $t('agileTraining.scrumSim.planningBullet3') }}</li>
            </ul>
          </div>
          <div class="sp__planning-meter">
            <div class="sp__meter-row">
              <span>{{ $t('agileTraining.scrumSim.plannedPts') }}:</span>
              <strong>{{ plannedPts }}</strong>
            </div>
            <div class="sp__meter-row">
              <span>{{ $t('agileTraining.scrumSim.teamCapacityTotal', { n: sprintDaysTotal }) }}:</span>
              <strong>{{ sprintCapacityTotal }}</strong>
            </div>
            <div class="sp__meter-bar">
              <div class="sp__meter-bar-fill" :style="{ width: plannedPct + '%' }" :class="{ over: plannedPts > sprintCapacityTotal }"></div>
            </div>
            <p class="sp__meter-note" v-if="plannedPts > sprintCapacityTotal">
              ⚠️ {{ $t('agileTraining.scrumSim.overCapacityWarn') }}
            </p>
          </div>
        </div>
        <div class="sp__actions">
          <button
            class="sp__btn sp__btn--primary"
            :disabled="sprintTasks.length === 0"
            @click="confirmPlanning"
          >
            {{ content.labels.confirm_planning }}
          </button>
        </div>
        <p class="sp__hint">
          💡 {{ $t('agileTraining.scrumSim.planningTap') }}
        </p>
      </section>

      <!-- PHASE: day N -->
      <section v-if="isDayPhase" class="sp__card">
        <h3>{{ $t('agileTraining.scrumSim.dayHeading', { n: state.current_day, total: sprintDaysTotal }) }}</h3>

        <!-- Recap of the previous day (apply_notes from last history entry) -->
        <div
          v-if="lastDayRecap && !recapDismissed[lastDayRecap.day]"
          class="sp__recap"
        >
          <div class="sp__recap-head">
            <span class="sp__recap-badge">📖 {{ $t('agileTraining.scrumSim.recapTitle', { n: lastDayRecap.day }) }}</span>
            <button class="sp__recap-close" @click="dismissRecap(lastDayRecap.day)" :title="$t('agileTraining.scrumSim.recapClose')">✕</button>
          </div>
          <ul class="sp__recap-list">
            <li v-for="(n, i) in lastDayRecap.notes" :key="i">• {{ n }}</li>
          </ul>
        </div>

        <!-- Step 1: Reveal event -->
        <div v-if="!pendingDay.event_applied" class="sp__day-step">
          <p class="sp__hint">{{ $t('agileTraining.scrumSim.dayBeforeEvent') }}</p>
          <button class="sp__btn sp__btn--primary" @click="revealEvent">
            📣 {{ content.labels.open_today_event }}
          </button>
        </div>
        <div v-else>
          <!-- Event banner -->
          <div class="sp__event">
            <div class="sp__event-head">
              <span class="sp__event-badge">{{ $t('agileTraining.scrumSim.eventOfTheDay') }}</span>
              <span class="sp__event-title">{{ pendingDay.event.title }}</span>
            </div>
            <p class="sp__event-desc">{{ pendingDay.event.description }}</p>
            <ul v-if="pendingDay.event.notes && pendingDay.event.notes.length" class="sp__bullets">
              <li v-for="(n, i) in pendingDay.event.notes" :key="i">{{ n }}</li>
            </ul>
          </div>

          <!-- Step 2: Daily + allocation -->
          <div class="sp__day-grid">
            <div class="sp__day-col">
              <h4>{{ $t('agileTraining.scrumSim.dailyTitle') }}</h4>
              <p class="sp__hint">{{ $t('agileTraining.scrumSim.dailyHint') }}</p>
              <ul class="sp__bullets">
                <li>{{ $t('agileTraining.scrumSim.dailyQ1') }}</li>
                <li>{{ $t('agileTraining.scrumSim.dailyQ2') }}</li>
                <li>{{ $t('agileTraining.scrumSim.dailyQ3') }}</li>
              </ul>
            </div>
            <div class="sp__day-col">
              <h4>
                {{ content.labels.choose_allocation }}
                <span class="sp__cap-chip">⚡ {{ state.capacity_today }} {{ content.labels.points }}</span>
              </h4>
              <p class="sp__hint">{{ $t('agileTraining.scrumSim.allocHint') }}</p>

              <!-- Pull from sprint backlog: players choose which task to start themselves. -->
              <div class="sp__pull">
                <div class="sp__pull-head">
                  <span>▶ {{ $t('agileTraining.scrumSim.canStartTitle') }}</span>
                  <small v-if="startableTasks.length">{{ $t('agileTraining.scrumSim.canStartHint') }}</small>
                </div>
                <div v-if="startableTasks.length === 0 && startableBlockedByDeps.length === 0" class="sp__pull-empty">
                  {{ $t('agileTraining.scrumSim.canStartEmpty') }}
                </div>
                <div v-else>
                  <div
                    v-for="t in startableTasks"
                    :key="t.key"
                    class="sp__pull-row"
                  >
                    <div class="sp__pull-name">
                      <span>{{ t.title }}</span>
                      <small>{{ $t('agileTraining.scrumSim.need') }}: {{ taskNeedLeft(t) }}</small>
                    </div>
                    <button
                      class="sp__btn sp__btn--primary sp__btn--tiny"
                      :disabled="startBusy === t.key"
                      @click="startTask(t.key)"
                    >
                      ▶ {{ $t('agileTraining.scrumSim.startTask') }}
                    </button>
                  </div>
                  <div
                    v-for="t in startableBlockedByDeps"
                    :key="t.key"
                    class="sp__pull-row sp__pull-row--locked"
                  >
                    <div class="sp__pull-name">
                      <span>🔒 {{ t.title }}</span>
                      <small>{{ $t('agileTraining.scrumSim.waitsFor') }}: {{ t.missing.join(', ') }}</small>
                    </div>
                    <button class="sp__btn sp__btn--tiny" disabled :title="$t('agileTraining.scrumSim.cannotStartYet')">
                      🔒
                    </button>
                  </div>
                </div>
              </div>

              <!-- Allocation: only tasks already in progress. -->
              <div v-if="workableTasks.length === 0" class="sp__empty-block">
                {{ $t('agileTraining.scrumSim.noInProgress') }}
              </div>
              <div v-else class="sp__alloc">
                <div class="sp__alloc-head">
                  <span>{{ $t('agileTraining.scrumSim.inProgressTitle') }}</span>
                  <button class="sp__btn sp__btn--ghost sp__btn--tiny" @click="autoAllocate" :title="$t('agileTraining.scrumSim.autoAllocateHint')">
                    ⚡ {{ $t('agileTraining.scrumSim.autoAllocate') }}
                  </button>
                </div>
                <div
                  v-for="(t, idx) in orderedWorkableTasks"
                  :key="t.key"
                  class="sp__alloc-row"
                >
                  <span class="sp__alloc-rank">{{ idx + 1 }}</span>
                  <div class="sp__alloc-reorder">
                    <button class="sp__btn sp__btn--tiny sp__btn--ghost" :disabled="idx === 0" @click="movePriority(t.key, -1)" :title="$t('agileTraining.scrumSim.moveUp')">▲</button>
                    <button class="sp__btn sp__btn--tiny sp__btn--ghost" :disabled="idx === orderedWorkableTasks.length - 1" @click="movePriority(t.key, +1)" :title="$t('agileTraining.scrumSim.moveDown')">▼</button>
                  </div>
                  <div class="sp__alloc-name">
                    <span>{{ t.title }}</span>
                    <small>{{ $t('agileTraining.scrumSim.need') }}: {{ taskNeedLeft(t) }}</small>
                    <button
                      v-if="canReturnTask(t)"
                      class="sp__pull-return"
                      :disabled="returnBusy === t.key"
                      @click="returnTask(t.key)"
                      :title="$t('agileTraining.scrumSim.returnHint')"
                    >
                      ↩ {{ $t('agileTraining.scrumSim.returnTask') }}
                    </button>
                  </div>
                  <div class="sp__alloc-controls">
                    <button class="sp__btn sp__btn--tiny" @click="addAlloc(t.key, -1)">−</button>
                    <span class="sp__alloc-val">{{ allocDraft[t.key] || 0 }}</span>
                    <button class="sp__btn sp__btn--tiny" @click="addAlloc(t.key, +1)">+</button>
                  </div>
                </div>
              </div>
              <div class="sp__alloc-sum" :class="{ over: allocTotal > state.capacity_today }">
                {{ $t('agileTraining.scrumSim.allocTotal') }}: {{ allocTotal }} / {{ state.capacity_today }}
                <span v-if="allocTotal < state.capacity_today" class="sp__alloc-slack">
                  ({{ $t('agileTraining.scrumSim.unused', { n: state.capacity_today - allocTotal }) }})
                </span>
              </div>
              <div class="sp__actions">
                <button class="sp__btn sp__btn--ghost sp__btn--tiny" @click="commitAllocation">
                  {{ $t('agileTraining.scrumSim.saveAlloc') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Step 3: Decision -->
          <div class="sp__decision">
            <h4>{{ content.labels.choose_decision }}</h4>
            <p class="sp__hint">{{ $t('agileTraining.scrumSim.decisionHint') }}</p>

            <!-- Banner while selecting a task on the board -->
            <div v-if="pendingDecisionChoosing" class="sp__decision-banner">
              <span class="sp__decision-banner-icon">🎯</span>
              <div class="sp__decision-banner-body">
                <strong>{{ $t('agileTraining.scrumSim.selectTaskForDecision', { title: pendingDecisionMeta ? pendingDecisionMeta.title : '' }) }}</strong>
                <span>{{ $t('agileTraining.scrumSim.selectTaskOnBoard') }}</span>
              </div>
              <button class="sp__btn sp__btn--ghost sp__btn--tiny" @click="cancelDecision">
                {{ $t('agileTraining.scrumSim.cancelDecision') }}
              </button>
            </div>

            <!-- Chosen task pill -->
            <div v-else-if="pendingDecisionTaskObj" class="sp__decision-chosen">
              <span class="sp__decision-chosen-tag">{{ pendingDecisionMeta ? pendingDecisionMeta.title : pendingDecisionKey }}</span>
              <span class="sp__decision-chosen-arrow">→</span>
              <span class="sp__decision-chosen-task">{{ pendingDecisionTaskObj.title }}</span>
              <button class="sp__btn sp__btn--ghost sp__btn--tiny" @click="changeDecisionTask">
                {{ $t('agileTraining.scrumSim.changeSelection') }}
              </button>
              <button class="sp__btn sp__btn--ghost sp__btn--tiny" @click="cancelDecision">
                {{ $t('agileTraining.scrumSim.cancelDecision') }}
              </button>
            </div>

            <div class="sp__decision-grid">
              <button
                v-for="d in content.decisions || []"
                :key="d.key"
                class="sp__decision-card"
                :class="{
                  'sp__decision-card--active': pendingDecisionKey === d.key,
                  'sp__decision-card--locked': !canUseDecision(d) && pendingDecisionKey !== d.key,
                }"
                :disabled="!canUseDecision(d) && pendingDecisionKey !== d.key"
                @click="pickDecision(d)"
                :title="decisionLockTitle(d)"
              >
                <strong>
                  {{ d.title }}
                  <span v-if="(d.allowed_roles || []).length" class="sp__role-badge" :class="rolesBadgeClass(d.allowed_roles)">
                    {{ rolesShortLabel(d.allowed_roles) }}
                  </span>
                </strong>
                <span>{{ d.desc }}</span>
                <em v-if="!canUseDecision(d) && pendingDecisionKey !== d.key" class="sp__decision-locked">
                  🔒 {{ decisionLockMessage(d) }}
                </em>
                <em v-else-if="d.needs_task && pendingDecisionKey === d.key">
                  {{ decisionTaskLabel() }}
                </em>
              </button>
            </div>
            <div v-if="roleToast" class="sp__role-toast">⚠️ {{ roleToast }}</div>
          </div>

          <!-- Step 4: Finish -->
          <div class="sp__actions sp__actions--end">
            <button class="sp__btn sp__btn--ghost" @click="askAi('daily')">🤖 {{ $t('agileTraining.scrumSim.askAi') }}</button>
            <button class="sp__btn sp__btn--primary" @click="endDay">
              {{ content.labels.finish_day }} →
            </button>
          </div>
        </div>
      </section>

      <!-- PHASE: review -->
      <section v-if="phase === 'review'" class="sp__card">
        <h3>🏁 {{ $t('agileTraining.scrumSim.reviewTitle') }}</h3>
        <div class="sp__review-metrics" v-if="state.review_metrics">
          <div class="sp__metric">
            <span class="sp__metric-val">{{ state.review_metrics.done_total }}</span>
            <span class="sp__metric-lab">{{ $t('agileTraining.scrumSim.tasksDone') }}</span>
          </div>
          <div class="sp__metric">
            <span class="sp__metric-val">{{ state.review_metrics.done_core }} / {{ state.review_metrics.total_core }}</span>
            <span class="sp__metric-lab">{{ $t('agileTraining.scrumSim.coreDone') }}</span>
          </div>
          <div class="sp__metric">
            <span class="sp__metric-val">{{ state.review_metrics.blocked }}</span>
            <span class="sp__metric-lab">{{ $t('agileTraining.scrumSim.stillBlocked') }}</span>
          </div>
          <div class="sp__metric">
            <span class="sp__metric-val">{{ state.review_metrics.rework }}</span>
            <span class="sp__metric-lab">{{ $t('agileTraining.scrumSim.reworkLeft') }}</span>
          </div>
        </div>
        <div class="sp__stakeholder" :class="'sp__stakeholder--' + (state.review_metrics && state.review_metrics.outcome)">
          <strong>{{ $t('agileTraining.scrumSim.stakeholderSays') }}:</strong>
          <p>{{ stakeholderText }}</p>
        </div>

        <!-- Expanded per-task breakdown -->
        <div v-if="reviewBreakdownGroups.length" class="sp__review-break">
          <h4 class="sp__review-subtitle">📋 {{ $t('agileTraining.scrumSim.reviewBreakdownTitle') }}</h4>
          <p class="sp__hint">{{ $t('agileTraining.scrumSim.reviewBreakdownHint') }}</p>

          <div v-if="reviewTotals" class="sp__review-totals">
            <span class="sp__totals-chip">{{ $t('agileTraining.scrumSim.totalDonePts') }}: <strong>{{ reviewTotals.done_points }}</strong></span>
            <span class="sp__totals-chip">{{ $t('agileTraining.scrumSim.totalScopedPts') }}: <strong>{{ reviewTotals.scoped_points }}</strong></span>
            <span class="sp__totals-chip" v-if="reviewTotals.extra_points > 0">{{ $t('agileTraining.scrumSim.reworkPtsChip') }}: <strong>+{{ reviewTotals.extra_points }}</strong></span>
            <span class="sp__totals-chip">{{ $t('agileTraining.scrumSim.eventsCount') }}: <strong>{{ reviewTotals.events_count }}</strong></span>
            <span class="sp__totals-chip">{{ $t('agileTraining.scrumSim.decisionsCount') }}: <strong>{{ reviewTotals.decisions_count }}</strong></span>
          </div>

          <div
            v-for="grp in reviewBreakdownGroups"
            :key="grp.bucket"
            class="sp__review-group"
            :class="'sp__review-group--' + grp.bucket"
          >
            <div class="sp__review-group-head">
              <span class="sp__review-group-icon">{{ grp.icon }}</span>
              <strong>{{ grp.label }}</strong>
              <span class="sp__review-group-count">{{ grp.rows.length }}</span>
            </div>
            <div class="sp__review-items">
              <div
                v-for="row in grp.rows"
                :key="row.key"
                class="sp__review-item"
              >
                <div class="sp__review-item-head">
                  <span class="sp__review-item-title">{{ row.title }}</span>
                  <span v-if="row.core" class="sb__badge sb__badge--core">{{ $t('agileTraining.scrumSim.core') }}</span>
                  <span v-else class="sb__badge sb__badge--opt">{{ $t('agileTraining.scrumSim.optional') }}</span>
                  <span v-if="row.origin === 'stakeholder'" class="sb__badge sb__badge--new">{{ $t('agileTraining.scrumSim.fromStakeholder') }}</span>
                  <span v-if="row.origin === 'split'" class="sb__badge sb__badge--split">{{ $t('agileTraining.scrumSim.split') }}</span>
                  <span v-if="row.risky" class="sb__badge sb__badge--risky">⚠ {{ $t('agileTraining.scrumSim.badges.risky') }}</span>
                  <span class="sp__review-item-pts">
                    {{ row.progress }}/{{ row.need }}{{ row.extra > 0 ? ' (+' + row.extra + ')' : '' }}
                  </span>
                </div>
                <div v-if="row.state_reason" class="sp__review-item-reason">{{ row.state_reason }}</div>
                <ul v-if="row.touches && row.touches.length" class="sp__review-touches">
                  <li
                    v-for="(touch, ti) in row.touches"
                    :key="ti"
                    class="sp__review-touch"
                    :class="'sp__review-touch--' + touch.kind"
                  >
                    <span class="sp__review-touch-day">День {{ touch.day }}</span>
                    <span class="sp__review-touch-icon">{{ touchIcon(touch) }}</span>
                    <span>{{ touchLabel(touch) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="sp__actions">
          <button class="sp__btn sp__btn--primary" @click="goToRetro">{{ content.labels.open_retro }} →</button>
        </div>
      </section>

      <!-- PHASE: retro -->
      <section v-if="phase === 'retro'" class="sp__card">
        <h3>🔁 {{ $t('agileTraining.scrumSim.retroTitle') }}</h3>
        <p class="sp__hint">{{ $t('agileTraining.scrumSim.retroHint') }}</p>
        <div class="sp__retro-grid">
          <button
            v-for="imp in content.improvements || []"
            :key="imp.key"
            class="sp__retro-item"
            :class="{ 'sp__retro-item--picked': (state.retro_picks || []).includes(imp.key) }"
            @click="toggleImprovement(imp.key)"
          >
            <strong>{{ imp.title }}</strong>
            <span>{{ imp.desc }}</span>
          </button>
        </div>
        <div class="sp__actions">
          <button class="sp__btn sp__btn--ghost" @click="askAi('retro')">🤖 {{ $t('agileTraining.scrumSim.askAi') }}</button>
          <button class="sp__btn sp__btn--primary" :disabled="(state.retro_picks || []).length === 0" @click="confirmRetro">
            {{ content.labels.open_summary }} →
          </button>
        </div>
      </section>

      <!-- PHASE: summary -->
      <section v-if="phase === 'summary'" class="sp__card">
        <h3>🎯 {{ $t('agileTraining.scrumSim.summaryTitle') }}</h3>
        <p>{{ $t('agileTraining.scrumSim.summaryLead') }}</p>

        <div class="sp__summary-grid">
          <div>
            <h4>{{ $t('agileTraining.scrumSim.summaryDone') }}</h4>
            <ul class="sp__bullets">
              <li v-for="t in tasksInCol('done')" :key="t.key">✅ {{ t.title }}</li>
              <li v-if="tasksInCol('done').length === 0">—</li>
            </ul>
          </div>
          <div>
            <h4>{{ $t('agileTraining.scrumSim.summaryNotDone') }}</h4>
            <ul class="sp__bullets">
              <li v-for="t in tasksNotDone" :key="t.key">
                {{ t.column === 'backlog' ? '📦' : t.column === 'in_progress' ? '🟡' : t.column === 'review' ? '🔵' : '📦' }}
                {{ t.title }}
                <em v-if="t.state === 'blocked'">— {{ $t('agileTraining.scrumSim.stillBlocked').toLowerCase() }}</em>
              </li>
              <li v-if="tasksNotDone.length === 0">—</li>
            </ul>
          </div>
        </div>

        <div v-if="(state.retro_picks || []).length" class="sp__retro-result">
          <h4>{{ $t('agileTraining.scrumSim.retroChosen') }}</h4>
          <ul class="sp__bullets">
            <li v-for="k in state.retro_picks" :key="k">
              <strong>{{ improvementTitle(k) }}.</strong> {{ improvementDesc(k) }}
            </li>
          </ul>
        </div>

        <h4>{{ $t('agileTraining.scrumSim.dailyLog') }}</h4>
        <ol class="sp__daily-log">
          <li v-for="d in state.days" :key="d.day">
            <strong>{{ $t('agileTraining.scrumSim.dayLabel', { n: d.day }) }}:</strong>
            {{ (d.event && d.event.title) || $t('agileTraining.scrumSim.uneventfulDay') }}
            <em>— {{ decisionSummary(d.decision) }}</em>
          </li>
        </ol>

        <div class="sp__actions">
          <button class="sp__btn sp__btn--ghost" @click="resetGame">{{ content.labels.reset }}</button>
          <router-link to="/agile-training" class="sp__btn sp__btn--ghost">
            ← {{ $t('agileTraining.hub.backHome') }}
          </router-link>
        </div>
      </section>

      <!-- Event popup -->
      <div v-if="eventPopupOpen" class="sp__modal-backdrop" @click.self="dismissEventPopup">
        <div class="sp__modal" role="dialog">
          <div class="sp__modal-head">
            <span class="sp__modal-badge">📣 {{ $t('agileTraining.scrumSim.eventOfTheDay') }}</span>
            <span class="sp__modal-day">{{ $t('agileTraining.scrumSim.dayLabel', { n: state.current_day }) }}</span>
            <button class="sp__btn sp__btn--tiny sp__btn--ghost" @click="dismissEventPopup">✕</button>
          </div>
          <h3 class="sp__modal-title">{{ eventPopupData.title }}</h3>
          <p class="sp__modal-desc">{{ eventPopupData.description }}</p>
          <div v-if="eventPopupData.notes && eventPopupData.notes.length" class="sp__modal-notes">
            <div class="sp__modal-notes-head">{{ $t('agileTraining.scrumSim.eventEffects') }}</div>
            <ul>
              <li v-for="(n, i) in eventPopupData.notes" :key="i">{{ n }}</li>
            </ul>
          </div>
          <div class="sp__actions">
            <button class="sp__btn sp__btn--primary" @click="dismissEventPopup">
              {{ $t('agileTraining.scrumSim.eventPopupCta') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Floating AI helper -->
      <div v-if="aiOpen" class="sp__ai-pop">
        <div class="sp__ai-head">
          <strong>🤖 {{ $t('agileTraining.scrumSim.aiHelperTitle') }}</strong>
          <button class="sp__btn sp__btn--tiny sp__btn--ghost" @click="aiOpen = false">✕</button>
        </div>
        <textarea class="sp__textarea" rows="3" v-model="aiInput" :placeholder="$t('agileTraining.scrumSim.aiPh')"></textarea>
        <div class="sp__ai-meta">
          {{ $t('agileTraining.scrumSim.aiRemaining', { n: Math.max(0, aiLimit - aiCalls) }) }}
        </div>
        <div class="sp__actions">
          <button class="sp__btn sp__btn--primary" :disabled="aiBusy" @click="sendAi">
            {{ aiBusy ? '…' : $t('agileTraining.scrumSim.aiSend') }}
          </button>
        </div>
        <div v-if="aiReply" class="sp__ai-reply">{{ aiReply }}</div>
      </div>
      <button v-else class="sp__ai-fab" @click="aiOpen = true" :title="$t('agileTraining.scrumSim.aiHelperTitle')">🤖</button>
    </template>

  </div>
  <div v-else class="sp__loading">{{ $t('common.loading') || 'Loading…' }}</div>
</template>

<script>
import axios from 'axios';
import ScrumBoard from '@/components/ScrumSim/ScrumBoard.vue';

const TOKEN_KEY_PREFIX = 'at_scrumsim_token_';
const NAME_KEY_PREFIX  = 'at_scrumsim_name_';
const POLL_INTERVAL_MS = 3500;

function read(prefix, slug) { try { return localStorage.getItem(prefix + slug) || ''; } catch (_) { return ''; } }
function write(prefix, slug, v) {
  try { if (v) localStorage.setItem(prefix + slug, v); else localStorage.removeItem(prefix + slug); } catch (_) { /* noop */ }
}

export default {
  name: 'AgileScrumSimPlay',
  components: { ScrumBoard },
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      loading: true,
      loadError: '',
      joining: false,
      joinError: '',

      locale: this.$i18n.locale || 'ru',
      group: null,
      sessionInfo: this.prefetchedSession,
      content: { context: {}, roles: [], tasks: [], events: [], decisions: [], improvements: [], labels: {} },
      state: null,

      participantToken: '',
      displayName: '',

      sprintGoalDraft: '',
      allocDraft: {},
      priorityOrder: [],
      pendingDecisionDraft: null,
      pulseKeys: [],
      flashMessage: '',
      recapDismissed: {},
      roleToast: '',

      showRoleDesc: false,

      aiOpen: false,
      aiInput: '',
      aiReply: '',
      aiBusy: false,
      aiLimit: 10,
      aiCalls: 0,

      pollTimer: null,
      lastVersion: 0,

      eventPopupOpen: false,
      eventPopupSeenKey: '',

      startBusy: '',
      returnBusy: '',
    };
  },
  computed: {
    phase() { return (this.state && this.state.phase) || 'lobby'; },
    isDayPhase() { return this.phase && this.phase.startsWith('day_'); },
    phaseClass() {
      if (this.isDayPhase) return 'day';
      return this.phase || 'lobby';
    },
    phaseLabel() {
      const map = {
        lobby:    this.$t('agileTraining.scrumSim.phases.lobby'),
        planning: this.$t('agileTraining.scrumSim.phases.planning'),
        review:   this.$t('agileTraining.scrumSim.phases.review'),
        retro:    this.$t('agileTraining.scrumSim.phases.retro'),
        summary:  this.$t('agileTraining.scrumSim.phases.summary'),
      };
      if (this.isDayPhase) return this.$t('agileTraining.scrumSim.phases.day', { n: this.state.current_day });
      return map[this.phase] || this.phase;
    },
    participantList() {
      if (!this.state || !this.state.participants) return [];
      return Object.entries(this.state.participants).map(([token, info]) => ({
        token, name: info.name, role: info.role,
      }));
    },
    participantsCount() { return this.participantList.length; },
    myRole() { return (this.state && this.state.my && this.state.my.role) || ''; },
    myRoleInfo() {
      if (!this.myRole) return null;
      return (this.content.roles || []).find(r => r.key === this.myRole) || null;
    },
    pendingDay() { return (this.state && this.state.pending_day) || {}; },
    pendingAllocation() { return (this.pendingDay && this.pendingDay.allocation) || {}; },
    boardColumns() {
      if (!this.content || !this.content.context || !this.content.context.columns) return undefined;
      return this.content.context.columns;
    },
    boardSelectable() {
      if (this.phase === 'planning') return true;
      if (this.isDayPhase && this.pendingDecisionChoosing) return true;
      return false;
    },
    pendingDecisionKey() {
      return (this.pendingDay && this.pendingDay.decision && this.pendingDay.decision.key) || '';
    },
    pendingDecisionTask() {
      return (this.pendingDay && this.pendingDay.decision && this.pendingDay.decision.task) || '';
    },
    pendingDecisionNeedsTask() {
      return ['swarm', 'split_task', 'descope', 'reduce_scope', 'escalate'].includes(this.pendingDecisionKey);
    },
    pendingDecisionChoosing() {
      return this.pendingDecisionNeedsTask && !this.pendingDecisionTask;
    },
    pendingDecisionColumnHint() {
      const k = this.pendingDecisionKey;
      if (k === 'split_task') return 'backlog';
      if (k === 'descope') return 'in_progress';
      if (k === 'escalate') return 'in_progress';
      if (k === 'swarm') return 'in_progress';
      if (k === 'reduce_scope') return '';
      return '';
    },
    pendingDecisionMeta() {
      const k = this.pendingDecisionKey;
      if (!k) return null;
      return (this.content.decisions || []).find(d => d.key === k) || null;
    },
    pendingDecisionTaskObj() {
      const tk = this.pendingDecisionTask;
      if (!tk || !this.state || !this.state.tasks) return null;
      return this.state.tasks.find(t => t.key === tk) || null;
    },
    selectedTaskKeys() {
      if (this.isDayPhase && this.pendingDecisionTask) {
        return [this.pendingDecisionTask];
      }
      return [];
    },
    highlightColumn() {
      if (this.isDayPhase && this.pendingDecisionChoosing) {
        return this.pendingDecisionColumnHint;
      }
      return '';
    },
    compactBoard() {
      return this.isDayPhase || this.phase === 'review' || this.phase === 'retro';
    },
    plannedPts() {
      if (!this.state) return 0;
      return this.sprintTasks.reduce((s, t) => s + (Number(t.complexity) || 0), 0);
    },
    plannedPct() {
      const cap = (this.state && this.state.team_capacity_per_day * 5) || 30;
      return Math.min(130, Math.round((this.plannedPts / Math.max(1, cap)) * 100));
    },
    sprintTasks() {
      if (!this.state) return [];
      return (this.state.tasks || []).filter(t => t.column !== 'product');
    },
    workableTasks() {
      if (!this.state) return [];
      const allTasks = this.state.tasks || [];
      const byKey = Object.fromEntries(allTasks.map(t => [t.key, t]));
      return allTasks.filter(t => {
        if (t.column !== 'in_progress') return false;
        if (t.state === 'blocked') return false;
        const depsReady = (t.deps || []).every(d => {
          const dep = byKey[d];
          if (!dep) return true;
          return ['done', 'review'].includes(dep.column);
        });
        return depsReady;
      });
    },
    startableTasks() {
      if (!this.state) return [];
      const allTasks = this.state.tasks || [];
      const byKey = Object.fromEntries(allTasks.map(t => [t.key, t]));
      return allTasks.filter(t => {
        if (t.column !== 'backlog') return false;
        if (t.state === 'blocked') return false;
        return (t.deps || []).every(d => {
          const dep = byKey[d];
          if (!dep) return true;
          return ['done', 'review'].includes(dep.column);
        });
      });
    },
    startableBlockedByDeps() {
      if (!this.state) return [];
      const allTasks = this.state.tasks || [];
      const byKey = Object.fromEntries(allTasks.map(t => [t.key, t]));
      return allTasks
        .filter(t => t.column === 'backlog' && t.state !== 'blocked')
        .filter(t => (t.deps || []).some(d => {
          const dep = byKey[d];
          return dep && !['done', 'review'].includes(dep.column);
        }))
        .map(t => ({
          key: t.key,
          title: t.title,
          complexity: t.complexity,
          missing: (t.deps || [])
            .map(d => byKey[d])
            .filter(dep => dep && !['done', 'review'].includes(dep.column))
            .map(dep => dep.title),
        }));
    },
    waitingTasks() {
      if (!this.state) return [];
      const allTasks = this.state.tasks || [];
      const byKey = Object.fromEntries(allTasks.map(t => [t.key, t]));
      return allTasks
        .filter(t => {
          if (!['backlog', 'in_progress'].includes(t.column)) return false;
          if (t.state === 'blocked') return false;
          return (t.deps || []).some(d => {
            const dep = byKey[d];
            return dep && !['done', 'review'].includes(dep.column);
          });
        })
        .map(t => ({
          key: t.key,
          title: t.title,
          blockers: (t.deps || [])
            .map(d => byKey[d])
            .filter(dep => dep && !['done', 'review'].includes(dep.column))
            .map(dep => ({ key: dep.key, title: dep.title, column: dep.column })),
        }));
    },
    waitingBlockerTitles() {
      const seen = new Set();
      const titles = [];
      for (const w of this.waitingTasks) {
        for (const b of w.blockers) {
          if (seen.has(b.key)) continue;
          seen.add(b.key);
          titles.push(b.title);
          if (titles.length >= 3) return titles;
        }
      }
      return titles;
    },
    showWaitingHint() {
      return this.waitingTasks.length > 0 && this.workableTasks.length < 3;
    },
    reviewBreakdownRows() {
      const rm = this.state && this.state.review_metrics;
      return (rm && rm.breakdown) || [];
    },
    reviewTotals() {
      const rm = this.state && this.state.review_metrics;
      return (rm && rm.totals) || null;
    },
    reviewBreakdownGroups() {
      const rows = this.reviewBreakdownRows;
      if (!rows.length) return [];
      const meta = {
        done:        { icon: '✅', label: this.$t('agileTraining.scrumSim.grpDone') },
        review:      { icon: '🔵', label: this.$t('agileTraining.scrumSim.grpReview') },
        in_progress: { icon: '🟡', label: this.$t('agileTraining.scrumSim.grpInProgress') },
        blocked:     { icon: '🔴', label: this.$t('agileTraining.scrumSim.grpBlocked') },
        not_started: { icon: '📦', label: this.$t('agileTraining.scrumSim.grpNotStarted') },
        descoped:    { icon: '➖', label: this.$t('agileTraining.scrumSim.grpDescoped') },
      };
      const order = ['done', 'review', 'in_progress', 'blocked', 'not_started', 'descoped'];
      const map = {};
      for (const row of rows) {
        const b = row.bucket;
        if (!map[b]) map[b] = [];
        map[b].push(row);
      }
      return order
        .filter(b => (map[b] || []).length)
        .map(b => ({ bucket: b, icon: meta[b].icon, label: meta[b].label, rows: map[b] }));
    },
    lastDayRecap() {
      const days = (this.state && this.state.days) || [];
      if (!days.length) return null;
      const last = days[days.length - 1];
      const curDay = (this.state && this.state.current_day) || 0;
      if (!last || last.day >= curDay) return null;
      const notes = (last.apply_notes || []).concat(last.risk_notes || []);
      const uniq = Array.from(new Set(notes));
      if (!uniq.length) return null;
      return { day: last.day, notes: uniq };
    },
    allocTotal() {
      return Object.values(this.allocDraft).reduce((s, v) => s + (Number(v) || 0), 0);
    },
    tasksNotDone() {
      return this.sprintTasks.filter(t => t.column !== 'done');
    },
    stakeholderText() {
      const o = this.state && this.state.review_metrics && this.state.review_metrics.outcome;
      return this.$t('agileTraining.scrumSim.stakeholderOutcome.' + (o || 'fail'));
    },
    sprintDaysTotal() {
      return (this.state && this.state.sprint_days) || 10;
    },
    sprintCapacityTotal() {
      if (!this.state) return 0;
      return (this.state.team_capacity_per_day || 6) * this.sprintDaysTotal;
    },
    orderedWorkableTasks() {
      const saved = (this.state && this.state.priority_order) || [];
      const local = this.priorityOrder || [];
      const priority = local.length ? local : saved;
      const byKey = Object.fromEntries(this.workableTasks.map(t => [t.key, t]));
      const seen = new Set();
      const out = [];
      for (const k of priority) {
        if (byKey[k] && !seen.has(k)) { out.push(byKey[k]); seen.add(k); }
      }
      for (const t of this.workableTasks) {
        if (!seen.has(t.key)) { out.push(t); seen.add(t.key); }
      }
      return out;
    },
    eventPopupData() {
      return (this.pendingDay && this.pendingDay.event) || { title: '', description: '', notes: [] };
    },
  },
  watch: {
    '$i18n.locale'(val) {
      if (val !== this.locale) { this.locale = val; this.reloadContent(); }
    },
    'pendingDay.event_applied'(val) {
      if (val) this.maybeOpenEventPopup();
    },
    'state.current_day'() {
      this.maybeOpenEventPopup();
    },
  },
  async mounted() {
    this.participantToken = read(TOKEN_KEY_PREFIX, this.slug);
    this.displayName = read(NAME_KEY_PREFIX, this.slug);
    try {
      await this.loadState(true);
    } catch (e) {
      this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
    } finally {
      this.loading = false;
    }
    this.startPolling();
  },
  beforeUnmount() { this.stopPolling(); },
  methods: {
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* noop */ }
    },
    startPolling() {
      this.stopPolling();
      this.pollTimer = setInterval(() => {
        this.loadState(false).catch(() => {});
      }, POLL_INTERVAL_MS);
    },
    stopPolling() {
      if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; }
    },
    async loadState(updateLocal) {
      const params = { locale: this.locale };
      if (this.participantToken) params.participant_token = this.participantToken;
      const res = await axios.get(`/api/agile-training/scrum-sim/g/${this.slug}/state`, { params });
      this.group = res.data.group;
      this.sessionInfo = res.data.session;
      this.content = res.data.content || this.content;
      const s = res.data.state;
      if (s) {
        if (!updateLocal && this.state && s.version === this.lastVersion) return;
        const prev = this.state;
        this.state = s;
        this.lastVersion = s.version;
        if (updateLocal || !prev) {
          this.sprintGoalDraft = s.sprint_goal || '';
          this.allocDraft = { ...(s.pending_day && s.pending_day.allocation || {}) };
          this.aiCalls = (s.my && s.my.ai_calls) || 0;
          this.aiLimit = (s.my && s.my.ai_calls_limit) || 10;
        } else {
          if (prev.pending_day && prev.pending_day.day !== s.pending_day.day) {
            this.allocDraft = { ...(s.pending_day.allocation || {}) };
          }
        }
      }
    },
    async reloadContent() {
      try {
        const r = await axios.get(`/api/agile-training/scrum-sim/content`, { params: { locale: this.locale } });
        this.content = r.data;
      } catch (_) { /* ignore */ }
    },
    async joinGroup() {
      this.joining = true;
      this.joinError = '';
      try {
        const body = { display_name: this.displayName || undefined };
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, body);
        this.participantToken = res.data.participant_token;
        write(TOKEN_KEY_PREFIX, this.slug, this.participantToken);
        write(NAME_KEY_PREFIX, this.slug, this.displayName);
        await this.loadState(true);
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.joining = false;
      }
    },
    async changeRole(role) {
      if (!this.participantToken) return;
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/join`, {
          participant_token: this.participantToken,
          role: role || null,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async startPlanning() {
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/planning`, {
        participant_token: this.participantToken,
      });
      await this.loadState(true);
    },
    async saveSprintGoal() {
      const g = (this.sprintGoalDraft || '').trim();
      if (!this.state || this.state.sprint_goal === g) return;
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/planning`, {
        participant_token: this.participantToken,
        sprint_goal: g,
      });
      await this.loadState(true);
    },
    async confirmPlanning() {
      await this.saveSprintGoal();
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/planning/confirm`, {
          participant_token: this.participantToken,
        });
        await this.loadState(true);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || 'Error');
      }
    },
    onBoardTaskClick(t) {
      if (this.phase === 'planning') {
        if (t.column === 'product') {
          this.planningPullChain(t);
          return;
        }
        if (t.column === 'backlog') {
          this.planningPush(t);
          return;
        }
        return;
      } else if (this.isDayPhase && this.pendingDecisionNeedsTask) {
        if (this.pendingDecisionKey === 'swarm' && t.column !== 'in_progress') {
          this.showRoleToast(this.$t('agileTraining.scrumSim.swarmOnlyInProgress'));
          return;
        }
        this.commitDecisionWithTask(t.key);
      }
    },
    async planningPullChain(t) {
      const depsInProduct = this.collectDepsInProduct(t.key);
      try {
        const res = await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/planning`, {
          participant_token: this.participantToken,
          action: depsInProduct.length ? 'pull_chain' : 'pull',
          task_key: t.key,
        });
        await this.loadState(true);
        const pulled = (res && res.data && res.data.pulled_chain) || [];
        if (pulled.length) {
          const titles = pulled.map(k => this.taskTitle(k)).join(', ');
          this.flashMessage = this.$t('agileTraining.scrumSim.pullChainFlash', { titles });
          this.pulseKeys = [t.key, ...pulled];
          setTimeout(() => { this.pulseKeys = []; }, 1400);
          setTimeout(() => { if (this.flashMessage) this.flashMessage = ''; }, 4500);
        }
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || 'Error');
      }
    },
    async planningPush(t) {
      const dependents = this.collectDependentsInSprint(t.key);
      if (dependents.length) {
        const titles = dependents.map(k => this.taskTitle(k)).join(', ');
        const ok = window.confirm(
          this.$t('agileTraining.scrumSim.pushWarnConfirm', { title: t.title, titles })
        );
        if (!ok) return;
      }
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/planning`, {
          participant_token: this.participantToken,
          action: 'push',
          task_key: t.key,
        });
        await this.loadState(true);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || 'Error');
      }
    },
    taskTitle(key) {
      const tasks = (this.state && this.state.tasks) || [];
      const f = tasks.find(x => x.key === key);
      return f ? f.title : key;
    },
    dismissRecap(day) {
      this.recapDismissed = { ...this.recapDismissed, [day]: true };
    },
    touchIcon(touch) {
      if (!touch) return '•';
      if (touch.kind === 'event') return '📣';
      if (touch.kind === 'alloc') return '⚙️';
      if (touch.kind === 'decision') {
        const m = {
          swarm: '👥', split_task: '✂️', descope: '➖',
          escalate: '📢', buffer_quality: '🛡️', continue: '▶️',
        };
        return m[touch.sub] || '🎯';
      }
      return '•';
    },
    touchLabel(touch) {
      if (!touch) return '';
      if (touch.kind === 'event') {
        const extra = touch.detail ? ` — ${touch.detail}` : '';
        return `${this.$t('agileTraining.scrumSim.touchEvent')}: ${touch.label}${extra}`;
      }
      if (touch.kind === 'alloc') {
        return this.$t('agileTraining.scrumSim.touchAlloc', { label: touch.label });
      }
      if (touch.kind === 'decision') {
        const dec = (this.content.decisions || []).find(d => d.key === touch.sub);
        const decTitle = dec ? dec.title : touch.sub;
        return `${this.$t('agileTraining.scrumSim.touchDecision')}: ${decTitle}`;
      }
      return touch.label || '';
    },
    collectDepsInProduct(rootKey) {
      const tasks = (this.state && this.state.tasks) || [];
      const byKey = {};
      for (const t of tasks) byKey[t.key] = t;
      const seen = new Set();
      const stack = [rootKey];
      const out = [];
      while (stack.length) {
        const k = stack.pop();
        if (seen.has(k)) continue;
        seen.add(k);
        const t = byKey[k];
        if (!t) continue;
        for (const d of (t.deps || [])) {
          const dep = byKey[d];
          if (dep && dep.column === 'product' && !seen.has(d)) {
            out.push(d);
            stack.push(d);
          }
        }
      }
      return out;
    },
    collectDependentsInSprint(key) {
      const tasks = (this.state && this.state.tasks) || [];
      const ins = ['backlog', 'in_progress', 'review'];
      return tasks
        .filter(t => (t.deps || []).includes(key) && ins.includes(t.column))
        .map(t => t.key);
    },
    async revealEvent() {
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/advance`, {
          participant_token: this.participantToken,
        });
        await this.loadState(true);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || 'Error');
      }
    },
    taskNeedLeft(t) {
      return Math.max(0, Number(t.complexity || 0) + Number(t.extra || 0) - Number(t.progress || 0));
    },
    addAlloc(key, d) {
      const cur = Number(this.allocDraft[key] || 0);
      const cap = (this.state && this.state.capacity_today) || 6;
      const taskObj = (this.state && this.state.tasks || []).find(t => t.key === key);
      const taskMax = taskObj ? this.taskNeedLeft(taskObj) : cap;
      const next = Math.max(0, Math.min(cap, Math.min(taskMax, cur + d)));
      this.allocDraft = { ...this.allocDraft, [key]: next };
    },
    movePriority(key, delta) {
      const list = this.orderedWorkableTasks.map(t => t.key);
      const idx = list.indexOf(key);
      if (idx < 0) return;
      const newIdx = idx + delta;
      if (newIdx < 0 || newIdx >= list.length) return;
      list.splice(newIdx, 0, list.splice(idx, 1)[0]);
      this.priorityOrder = list;
    },
    autoAllocate() {
      const cap = (this.state && this.state.capacity_today) || 6;
      let left = cap;
      const next = {};
      for (const t of this.orderedWorkableTasks) {
        if (left <= 0) break;
        const need = this.taskNeedLeft(t);
        const take = Math.min(need, left);
        if (take > 0) next[t.key] = take;
        left -= take;
      }
      this.allocDraft = next;
    },
    async commitAllocation() {
      const clean = {};
      for (const [k, v] of Object.entries(this.allocDraft)) {
        if (Number(v) > 0) clean[k] = Number(v);
      }
      const order = (this.priorityOrder && this.priorityOrder.length)
        ? this.priorityOrder
        : ((this.state && this.state.priority_order) || []);
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/allocate`, {
        participant_token: this.participantToken,
        allocation: clean,
        priority_order: order,
      });
      await this.loadState(true);
    },
    canReturnTask(t) {
      if (!t) return false;
      if (t.column !== 'in_progress') return false;
      if (Number(t.progress || 0) > 0) return false;
      if (t.state === 'blocked') return false;
      return true;
    },
    async startTask(key) {
      if (!key || this.startBusy) return;
      this.startBusy = key;
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/task/start`, {
          participant_token: this.participantToken,
          task_key: key,
        });
        await this.loadState(true);
      } catch (e) {
        const data = e && e.response && e.response.data;
        if (data && data.error === 'deps not ready' && Array.isArray(data.missing) && data.missing.length) {
          alert(this.$t('agileTraining.scrumSim.startBlockedByDeps', { names: data.missing.join(', ') }));
        } else {
          alert((data && data.error) || 'Error');
        }
      } finally {
        this.startBusy = '';
      }
    },
    async returnTask(key) {
      if (!key || this.returnBusy) return;
      this.returnBusy = key;
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/task/return`, {
          participant_token: this.participantToken,
          task_key: key,
        });
        await this.loadState(true);
      } catch (e) {
        alert((e && e.response && e.response.data && e.response.data.error) || 'Error');
      } finally {
        this.returnBusy = '';
      }
    },
    maybeOpenEventPopup() {
      if (!this.state || !this.isDayPhase) return;
      const pd = this.pendingDay || {};
      if (!pd.event_applied || !pd.event) return;
      const key = `sp_evt_seen_${this.slug}_${this.state.current_day}`;
      try {
        if (localStorage.getItem(key) === '1') return;
      } catch (_) { /* noop */ }
      this.eventPopupOpen = true;
      this.eventPopupSeenKey = key;
    },
    dismissEventPopup() {
      this.eventPopupOpen = false;
      try { if (this.eventPopupSeenKey) localStorage.setItem(this.eventPopupSeenKey, '1'); } catch (_) { /* noop */ }
    },
    canUseDecision(d) {
      if (!d) return false;
      if (d.key === 'swarm' && this.state && this.state.swarm_used_sprint) return false;
      if (d.key === 'reduce_scope' && this.state && this.state.reduce_scope_used_sprint) return false;
      const allowed = d.allowed_roles || [];
      if (!allowed.length) return true;
      if (this.myRole && allowed.includes(this.myRole)) return true;
      const teamRoles = new Set((this.participantList || []).map(p => p.role).filter(Boolean));
      let fallback = true;
      for (const r of allowed) { if (teamRoles.has(r)) { fallback = false; break; } }
      return fallback;
    },
    decisionLockMessage(d) {
      if (!d) return '';
      if (d.key === 'swarm' && this.state && this.state.swarm_used_sprint) {
        return this.$t('agileTraining.scrumSim.sprintLimitSwarm');
      }
      if (d.key === 'reduce_scope' && this.state && this.state.reduce_scope_used_sprint) {
        return this.$t('agileTraining.scrumSim.sprintLimitReduceScope');
      }
      return this.$t('agileTraining.scrumSim.roleRequiredHint', { roles: this.rolesLabelOf(d.allowed_roles) });
    },
    decisionLockTitle(d) {
      if (!d || this.canUseDecision(d)) return '';
      return this.decisionLockMessage(d);
    },
    rolesShortLabel(roles) {
      const r = (roles && roles[0]) || '';
      const short = {
        product_owner: 'PO', scrum_master: 'SM', developer: this.$t('agileTraining.scrumSim.roleShort.dev'),
      };
      if (roles && roles.length > 1 && (roles.length === 3)) return this.$t('agileTraining.scrumSim.roleShort.any');
      return short[r] || r || '';
    },
    rolesBadgeClass(roles) {
      const r = (roles && roles[0]) || '';
      if (roles && roles.length > 1) return 'sp__role-badge--any';
      return 'sp__role-badge--' + (r || '');
    },
    rolesLabelOf(roles) {
      if (!roles || !roles.length) return '';
      return roles.map(r => this.roleLabel(r)).join(' / ');
    },
    async pickDecision(d) {
      if (!this.canUseDecision(d)) {
        if (d.key === 'swarm' && this.state && this.state.swarm_used_sprint) {
          this.showRoleToast(this.$t('agileTraining.scrumSim.sprintLimitSwarm'));
        } else if (d.key === 'reduce_scope' && this.state && this.state.reduce_scope_used_sprint) {
          this.showRoleToast(this.$t('agileTraining.scrumSim.sprintLimitReduceScope'));
        } else {
          this.showRoleToast(this.$t('agileTraining.scrumSim.roleRequiredHint', { roles: this.rolesLabelOf(d.allowed_roles) }));
        }
        return;
      }
      this.roleToast = '';
      try {
        if (d.needs_task) {
          this.pendingDecisionDraft = d.key;
          await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/decision`, {
            participant_token: this.participantToken,
            decision_key: d.key, task_key: null,
          });
        } else {
          await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/decision`, {
            participant_token: this.participantToken,
            decision_key: d.key,
          });
        }
        await this.loadState(true);
      } catch (e) {
        this.handleDecisionError(e);
      }
    },
    async commitDecisionWithTask(taskKey) {
      const k = this.pendingDecisionKey;
      if (!k) return;
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/decision`, {
          participant_token: this.participantToken,
          decision_key: k, task_key: taskKey,
        });
        await this.loadState(true);
      } catch (e) {
        this.handleDecisionError(e);
      }
    },
    async cancelDecision() {
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/decision`, {
          participant_token: this.participantToken,
          decision_key: 'continue', task_key: null,
        });
        await this.loadState(true);
      } catch (_) { /* noop */ }
    },
    async changeDecisionTask() {
      const k = this.pendingDecisionKey;
      if (!k) return;
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/decision`, {
          participant_token: this.participantToken,
          decision_key: k, task_key: null,
        });
        await this.loadState(true);
      } catch (e) {
        this.handleDecisionError(e);
      }
    },
    handleDecisionError(e) {
      const data = (e && e.response && e.response.data) || {};
      if ((data.message || '').includes('role_requires') || data.error === 'role_required') {
        const roles = data.required_roles || [];
        this.showRoleToast(this.$t('agileTraining.scrumSim.roleRequiredHint', { roles: this.rolesLabelOf(roles) }));
      } else {
        this.showRoleToast(data.error || this.$t('agileTraining.scrumSim.genericError'));
      }
    },
    showRoleToast(msg) {
      this.roleToast = msg;
      clearTimeout(this._roleToastTimer);
      this._roleToastTimer = setTimeout(() => { this.roleToast = ''; }, 5000);
    },
    decisionTaskLabel() {
      const tk = this.pendingDecisionTask;
      if (tk) {
        const t = (this.state && this.state.tasks || []).find(x => x.key === tk);
        return t ? this.$t('agileTraining.scrumSim.selectedTask', { title: t.title }) : '';
      }
      return this.$t('agileTraining.scrumSim.selectTaskOnBoard');
    },
    async endDay() {
      await this.commitAllocation();
      try {
        await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/day/end`, {
          participant_token: this.participantToken,
        });
        this.allocDraft = {};
        await this.loadState(true);
        this.pulseKeys = [];
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || 'Error');
      }
    },
    async goToRetro() {
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/review/confirm`, {
        participant_token: this.participantToken,
      });
      await this.loadState(true);
    },
    async toggleImprovement(key) {
      const picks = (this.state && this.state.retro_picks) || [];
      const next = picks.includes(key) ? picks.filter(k => k !== key) : (picks.length >= 3 ? picks : [...picks, key]);
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/retro`, {
        participant_token: this.participantToken,
        picks: next,
      });
      await this.loadState(true);
    },
    async confirmRetro() {
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/retro`, {
        participant_token: this.participantToken,
        picks: this.state.retro_picks || [],
        confirm: true,
      });
      await this.loadState(true);
    },
    async resetGame() {
      if (!confirm(this.$t('agileTraining.scrumSim.resetConfirm'))) return;
      await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/reset`, {
        participant_token: this.participantToken,
      });
      await this.loadState(true);
    },
    async sendAi() {
      if (!this.aiInput.trim()) return;
      this.aiBusy = true;
      try {
        const res = await axios.post(`/api/agile-training/scrum-sim/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken,
          mode: this.isDayPhase ? 'daily' : this.phase,
          user_input: this.aiInput,
        });
        this.aiReply = res.data.reply || '';
        this.aiCalls = res.data.calls || this.aiCalls;
      } catch (e) {
        this.aiReply = (e.response && e.response.data && e.response.data.message) || 'Error';
      } finally {
        this.aiBusy = false;
      }
    },
    askAi(mode) {
      this.aiOpen = true;
      this.aiInput = this.aiInput || (mode === 'retro'
        ? this.$t('agileTraining.scrumSim.aiSeedRetro')
        : this.$t('agileTraining.scrumSim.aiSeedDaily'));
    },
    tasksInCol(col) {
      return (this.state.tasks || []).filter(t => t.column === col);
    },
    improvementTitle(key) {
      const i = (this.content.improvements || []).find(x => x.key === key);
      return i ? i.title : key;
    },
    improvementDesc(key) {
      const i = (this.content.improvements || []).find(x => x.key === key);
      return i ? i.desc : '';
    },
    roleLabel(key) {
      const r = (this.content.roles || []).find(x => x.key === key);
      return r ? r.title : key;
    },
    decisionSummary(d) {
      if (!d || !d.key) return this.$t('agileTraining.scrumSim.noDecision');
      const dc = (this.content.decisions || []).find(x => x.key === d.key);
      const title = dc ? dc.title : d.key;
      if (d.task) {
        const t = (this.state.tasks || []).find(x => x.key === d.task);
        return `${title}${t ? ': ' + t.title : ''}`;
      }
      return title;
    },
  },
};
</script>

<style scoped>
.sp { max-width: 1200px; margin: 0 auto; padding: 12px 14px 60px; }
.sp__loading { padding: 60px; text-align: center; color: #64748b; }

.sp__head {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 6px 0 14px; border-bottom: 1px solid #e2e8f0; margin-bottom: 12px;
}
.sp__head h1 { font-size: 20px; margin: 0; color: #0f172a; }
.sp__sub { margin: 2px 0 0; font-size: 12px; color: #64748b; }
.sp__sub-grp { font-weight: 600; color: #334155; }
.sp__head-right { display: flex; gap: 6px; align-items: center; }
.sp__phase-chip {
  font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px;
  background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc;
}
.sp__phase-chip--day { background: #dcfce7; color: #166534; border-color: #86efac; }
.sp__phase-chip--review { background: #ede9fe; color: #5b21b6; border-color: #c4b5fd; }
.sp__phase-chip--retro { background: #fce7f3; color: #9d174d; border-color: #f9a8d4; }
.sp__phase-chip--summary { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
.sp__lang {
  padding: 3px 10px; border-radius: 8px; background: #f1f5f9; color: #475569;
  border: 1px solid #cbd5e1; font-weight: 600; cursor: pointer; font-size: 12px;
}
.sp__lang.active { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }

.sp__err { background: #fee2e2; color: #991b1b; padding: 8px 12px; border-radius: 8px; margin: 8px 0; font-size: 13px; }

.sp__join {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 20px 22px; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}
.sp__join h2 { margin: 0 0 6px; font-size: 18px; }
.sp__story-line { color: #475569; font-size: 14px; line-height: 1.45; }
.sp__join-row { display: flex; gap: 8px; margin-top: 10px; }
.sp__input {
  flex: 1; padding: 9px 12px; border-radius: 10px; border: 1px solid #cbd5e1;
  font-size: 14px; background: #fff; color: #0f172a;
}
.sp__input:focus { outline: none; border-color: #0ea5e9; box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15); }

.sp__btn {
  padding: 9px 16px; border-radius: 10px; border: 1px solid transparent;
  font-weight: 600; cursor: pointer; font-size: 13px; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px; transition: all 0.15s;
}
.sp__btn--primary { background: #0ea5e9; color: #fff; }
.sp__btn--primary:hover:not(:disabled) { background: #0284c7; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(14, 165, 233, 0.3); }
.sp__btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.sp__btn--ghost { background: #fff; border-color: #cbd5e1; color: #475569; text-decoration: none; }
.sp__btn--ghost:hover:not(:disabled) { border-color: #0ea5e9; color: #0ea5e9; }
.sp__btn--tiny { padding: 3px 8px; font-size: 11px; border-radius: 6px; min-height: 0; }

.sp__team {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 8px 12px; background: #f1f5f9; border-radius: 10px; margin: 8px 0;
  flex-wrap: wrap;
}
.sp__team-members { display: flex; flex-wrap: wrap; gap: 6px; }
.sp__member {
  background: #fff; border: 1px solid #cbd5e1; border-radius: 999px;
  padding: 3px 10px; font-size: 12px; display: flex; align-items: center; gap: 6px;
}
.sp__member--me { border-color: #0ea5e9; background: #e0f2fe; color: #0369a1; font-weight: 600; }
.sp__member-name { font-weight: 600; }
.sp__member-role { color: #64748b; font-size: 11px; }
.sp__team-my-role { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; }
.sp__select {
  padding: 5px 10px; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff;
  font-size: 13px; color: #0f172a; font-family: inherit;
}
.sp__role-desc { background: #fef3c7; border: 1px solid #fcd34d; color: #78350f; font-size: 13px;
  padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; line-height: 1.45; }

.sp__board-wrap { margin: 10px 0 14px; }
.sp__board-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 6px; }
.sp__board-head h3 { font-size: 15px; margin: 0; color: #0f172a; }
.sp__goal-chip {
  background: linear-gradient(135deg, #fef3c7, #fde68a); border: 1px solid #facc15;
  color: #78350f; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
}

.sp__card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; }
.sp__card h3 { margin: 0 0 8px; font-size: 16px; color: #0f172a; }
.sp__card h4 { margin: 10px 0 6px; font-size: 14px; color: #334155; }
.sp__hint { color: #64748b; font-size: 13px; line-height: 1.45; margin: 4px 0 10px; }
.sp__bullets { padding-left: 20px; color: #334155; font-size: 13px; line-height: 1.5; margin: 6px 0; }

.sp__label { display: block; font-size: 12px; color: #64748b; font-weight: 600; margin: 6px 0 4px; text-transform: uppercase; letter-spacing: 0.02em; }
.sp__textarea {
  width: 100%; box-sizing: border-box; padding: 10px 12px; border-radius: 10px;
  border: 1px solid #cbd5e1; font-size: 14px; font-family: inherit; resize: vertical;
  background: #fff; color: #0f172a; line-height: 1.4;
}
.sp__textarea:focus { outline: none; border-color: #0ea5e9; box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15); }

.sp__planning-help { display: grid; grid-template-columns: 1fr auto; gap: 18px; margin-top: 10px; }
.sp__planning-meter {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px;
  min-width: 200px;
}
.sp__meter-row { display: flex; justify-content: space-between; font-size: 13px; color: #475569; }
.sp__meter-bar { height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden; margin: 8px 0 4px; }
.sp__meter-bar-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #0ea5e9); border-radius: 999px; transition: width 0.3s; }
.sp__meter-bar-fill.over { background: linear-gradient(90deg, #f97316, #ef4444); }
.sp__meter-note { font-size: 11px; color: #b91c1c; margin: 4px 0 0; }
.sp__actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.sp__actions--end { justify-content: flex-end; border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 12px; }

.sp__event {
  background: linear-gradient(135deg, #fef3c7, #fed7aa); border: 1px solid #fb923c;
  border-radius: 12px; padding: 12px 16px; margin: 8px 0 14px;
}
.sp__event-head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.sp__event-badge { background: #ea580c; color: #fff; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.sp__event-title { font-weight: 700; color: #7c2d12; font-size: 15px; }
.sp__event-desc { color: #78350f; font-size: 13px; line-height: 1.45; margin: 6px 0; }

.sp__day-step { padding: 20px 0; text-align: center; }
.sp__day-grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 16px; }
.sp__day-col h4 { display: flex; justify-content: space-between; align-items: center; }
.sp__cap-chip { font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 999px; font-weight: 700; }

.sp__pull {
  margin: 8px 0 12px;
  padding: 8px 10px 10px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
}
.sp__pull-head {
  display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
  font-size: 12px; font-weight: 700; color: #0f172a; padding: 2px 0 6px;
}
.sp__pull-head small { font-weight: 500; color: #64748b; font-size: 11px; }
.sp__pull-empty { color: #94a3b8; font-size: 12px; padding: 6px 0; }
.sp__pull-row {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 10px; margin-top: 4px;
}
.sp__pull-row--locked { background: #f1f5f9; border-style: dashed; }
.sp__pull-name { flex: 1; min-width: 0; display: flex; flex-direction: column; font-size: 13px; }
.sp__pull-name span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp__pull-name small { color: #94a3b8; font-size: 11px; margin-top: 1px; }
.sp__pull-return {
  align-self: flex-start; margin-top: 2px;
  font-size: 10px; line-height: 1; padding: 2px 6px;
  background: transparent; border: 1px solid #e2e8f0; border-radius: 6px;
  color: #64748b; cursor: pointer;
}
.sp__pull-return:hover:not(:disabled) { border-color: #94a3b8; color: #334155; }
.sp__pull-return:disabled { opacity: 0.5; cursor: not-allowed; }

.sp__alloc { display: flex; flex-direction: column; gap: 4px; margin: 6px 0; }
.sp__alloc-head {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;
  letter-spacing: 0.04em; padding: 4px 2px;
}
.sp__alloc-row {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 10px;
}
.sp__alloc-rank {
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  background: #e0f2fe; color: #0369a1; border-radius: 50%; font-size: 11px; font-weight: 700;
}
.sp__alloc-reorder { display: flex; flex-direction: column; gap: 2px; }
.sp__alloc-reorder .sp__btn { padding: 0 6px; font-size: 9px; line-height: 1; min-height: 14px; }
.sp__alloc-name { flex: 1; font-size: 13px; display: flex; flex-direction: column; min-width: 0; }
.sp__alloc-name span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp__alloc-name small { color: #94a3b8; font-size: 11px; margin-top: 1px; }
.sp__alloc-controls { display: flex; align-items: center; gap: 6px; }
.sp__alloc-val { min-width: 22px; text-align: center; font-weight: 700; color: #0f172a; font-variant-numeric: tabular-nums; }
.sp__alloc-sum { font-size: 13px; font-weight: 600; color: #334155; margin-top: 8px; text-align: right; }
.sp__alloc-sum.over { color: #b91c1c; }
.sp__alloc-slack { color: #94a3b8; font-weight: 500; font-size: 12px; margin-left: 6px; }

.sp__decision { margin-top: 14px; border-top: 1px solid #e2e8f0; padding-top: 12px; }
.sp__decision-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; }
.sp__decision-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 10px 12px; text-align: left; cursor: pointer;
  display: flex; flex-direction: column; gap: 4px;
  font-family: inherit; transition: all 0.15s;
}
.sp__decision-card strong { font-size: 13px; color: #0f172a; }
.sp__decision-card span { font-size: 12px; color: #64748b; line-height: 1.4; }
.sp__decision-card em { font-size: 11px; color: #0369a1; font-style: normal; font-weight: 600; }
.sp__decision-card:hover { border-color: #0ea5e9; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); }
.sp__decision-card--active { border-color: #0ea5e9; background: #e0f2fe; box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2); }
.sp__decision-card--locked { opacity: 0.55; cursor: not-allowed; background: #f8fafc; }
.sp__decision-card--locked:hover { border-color: #e2e8f0; transform: none; box-shadow: none; }
.sp__decision-card strong { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sp__decision-locked { color: #b91c1c !important; font-weight: 600; }

.sp__role-badge {
  font-size: 10px; padding: 1px 7px; border-radius: 999px; font-weight: 700;
  letter-spacing: 0.03em; text-transform: uppercase; border: 1px solid transparent;
}
.sp__role-badge--product_owner { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
.sp__role-badge--scrum_master  { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
.sp__role-badge--developer     { background: #dcfce7; color: #166534; border-color: #86efac; }
.sp__role-badge--any           { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }

.sp__decision-banner {
  display: flex; align-items: center; gap: 10px;
  background: linear-gradient(135deg, #fff7ed, #fde68a);
  border: 1px solid #f59e0b; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 10px;
  animation: sp-banner-pulse 2s ease-in-out infinite;
}
@keyframes sp-banner-pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.15); }
  50%     { box-shadow: 0 0 0 6px rgba(249, 115, 22, 0.00); }
}
.sp__decision-banner-icon { font-size: 22px; }
.sp__decision-banner-body { flex: 1; display: flex; flex-direction: column; }
.sp__decision-banner-body strong { font-size: 13px; color: #7c2d12; }
.sp__decision-banner-body span { font-size: 12px; color: #92400e; }

.sp__decision-chosen {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 10px;
  padding: 8px 12px; margin-bottom: 10px; font-size: 13px;
}
.sp__decision-chosen-tag { background: #059669; color: #fff; padding: 2px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }
.sp__decision-chosen-arrow { color: #64748b; font-weight: 700; }
.sp__decision-chosen-task { font-weight: 600; color: #064e3b; flex: 1; }

.sp__role-toast {
  background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b;
  padding: 8px 12px; border-radius: 10px; font-size: 13px; margin-top: 10px;
}
.sp__empty-block { color: #94a3b8; font-size: 13px; padding: 16px; text-align: center; background: #f8fafc; border-radius: 8px; }
.sp__waiting-hint {
  display: flex; align-items: flex-start; gap: 8px;
  margin: 6px 0 10px;
  padding: 8px 12px;
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  color: #475569;
  font-size: 12px;
  line-height: 1.35;
}
.sp__waiting-icon { font-size: 14px; flex-shrink: 0; }

.sp__review-metrics {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px; margin: 10px 0;
}
.sp__metric {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 10px; text-align: center;
}
.sp__metric-val { display: block; font-size: 22px; font-weight: 700; color: #0f172a; }
.sp__metric-lab { display: block; font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.03em; margin-top: 4px; }

.sp__flash {
  padding: 10px 14px; border-radius: 10px; margin: 8px 0 12px;
  font-size: 13px; line-height: 1.4;
  animation: sp-flash-in 0.25s ease-out both;
}
.sp__flash--chain { background: #fef3c7; border: 1px solid #fde68a; color: #92400e; }
@keyframes sp-flash-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.sp__planning-depshint { background: #eff6ff; border: 1px dashed #bfdbfe; border-radius: 8px; padding: 6px 10px; color: #1d4ed8; }

.sp__recap {
  background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
  padding: 10px 12px; margin-bottom: 10px;
}
.sp__recap-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.sp__recap-badge { font-weight: 700; color: #92400e; font-size: 13px; }
.sp__recap-close {
  background: transparent; border: none; font-size: 16px; color: #92400e;
  cursor: pointer; padding: 0 4px; line-height: 1;
}
.sp__recap-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 3px; font-size: 13px; color: #78350f; }

.sp__review-break { margin-top: 18px; padding-top: 12px; border-top: 1px dashed #e2e8f0; }
.sp__review-subtitle { margin: 0 0 4px; font-size: 15px; color: #0f172a; }
.sp__review-totals { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; }
.sp__totals-chip {
  background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 999px;
  padding: 3px 10px; font-size: 12px; color: #334155;
}
.sp__totals-chip strong { color: #0f172a; margin-left: 2px; }
.sp__review-group {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 10px 12px; margin-bottom: 10px;
}
.sp__review-group--done { background: #f0fdf4; border-color: #bbf7d0; }
.sp__review-group--blocked { background: #fef2f2; border-color: #fecaca; }
.sp__review-group--descoped { background: #f1f5f9; border-color: #cbd5e1; }
.sp__review-group--review { background: #f5f3ff; border-color: #ddd6fe; }
.sp__review-group-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 14px; color: #0f172a; }
.sp__review-group-icon { font-size: 16px; }
.sp__review-group-count {
  margin-left: auto; background: #fff; border: 1px solid #cbd5e1;
  border-radius: 999px; padding: 1px 8px; font-size: 11px; color: #475569;
}
.sp__review-items { display: flex; flex-direction: column; gap: 8px; }
.sp__review-item {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 8px 10px;
}
.sp__review-item-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.sp__review-item-title { font-weight: 600; color: #0f172a; font-size: 13px; margin-right: 6px; }
.sp__review-item-pts {
  margin-left: auto; font-variant-numeric: tabular-nums; font-size: 12px; color: #0369a1;
  background: #e0f2fe; padding: 1px 8px; border-radius: 999px; font-weight: 600;
}
.sp__review-item-reason { font-size: 12px; color: #b45309; margin-top: 4px; }
.sp__review-touches {
  list-style: none; padding: 0; margin: 6px 0 0;
  display: flex; flex-direction: column; gap: 3px;
  font-size: 12px; color: #475569;
}
.sp__review-touch { display: flex; align-items: center; gap: 6px; }
.sp__review-touch-day {
  background: #f1f5f9; color: #475569;
  padding: 1px 6px; border-radius: 6px; font-size: 11px; font-variant-numeric: tabular-nums;
  min-width: 58px; text-align: center;
}
.sp__review-touch--event .sp__review-touch-day { background: #fef3c7; color: #92400e; }
.sp__review-touch--decision .sp__review-touch-day { background: #ede9fe; color: #5b21b6; }
.sp__review-touch--alloc .sp__review-touch-day { background: #dbeafe; color: #1e40af; }

.sp__stakeholder { padding: 12px 14px; border-radius: 10px; margin: 10px 0; font-size: 14px; line-height: 1.5; }
.sp__stakeholder p { margin: 4px 0 0; }
.sp__stakeholder--great { background: #dcfce7; border: 1px solid #86efac; color: #166534; }
.sp__stakeholder--ok    { background: #e0f2fe; border: 1px solid #7dd3fc; color: #075985; }
.sp__stakeholder--rough { background: #fef3c7; border: 1px solid #fcd34d; color: #92400e; }
.sp__stakeholder--fail  { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; }

.sp__retro-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; }
.sp__retro-item {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 10px 12px; cursor: pointer; text-align: left;
  display: flex; flex-direction: column; gap: 4px; font-family: inherit; transition: all 0.15s;
}
.sp__retro-item strong { color: #0f172a; font-size: 13px; }
.sp__retro-item span { color: #64748b; font-size: 12px; line-height: 1.4; }
.sp__retro-item:hover { border-color: #0ea5e9; transform: translateY(-1px); }
.sp__retro-item--picked { background: #dcfce7; border-color: #22c55e; }

.sp__summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 10px 0; }
.sp__daily-log { padding-left: 22px; font-size: 13px; color: #334155; line-height: 1.6; }
.sp__daily-log em { color: #64748b; font-style: normal; }
.sp__retro-result { background: #f0fdf4; border: 1px solid #86efac; border-radius: 10px; padding: 10px 14px; margin-top: 10px; }

.sp__ai-fab {
  position: fixed; bottom: 24px; right: 24px; width: 52px; height: 52px;
  border-radius: 50%; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #fff;
  border: none; font-size: 24px; cursor: pointer; z-index: 100;
  box-shadow: 0 6px 18px rgba(14, 165, 233, 0.4);
}
.sp__ai-fab:hover { transform: translateY(-2px) scale(1.05); }
.sp__ai-pop {
  position: fixed; bottom: 24px; right: 24px; width: 340px; max-width: calc(100vw - 32px);
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 14px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18); z-index: 100;
}
.sp__ai-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.sp__ai-meta { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.sp__ai-reply {
  background: #f1f5f9; padding: 10px 12px; border-radius: 8px; font-size: 13px;
  line-height: 1.5; color: #334155; margin-top: 10px; white-space: pre-wrap;
}

.sp__modal-backdrop {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 200; padding: 20px; backdrop-filter: blur(2px);
  animation: sp-modal-fade 0.2s ease-out;
}
@keyframes sp-modal-fade { from { opacity: 0; } to { opacity: 1; } }
.sp__modal {
  background: #fff; border-radius: 16px; max-width: 520px; width: 100%;
  padding: 18px 22px; box-shadow: 0 20px 60px rgba(15, 23, 42, 0.35);
  border: 2px solid #f59e0b;
  animation: sp-modal-pop 0.25s cubic-bezier(.2,.9,.3,1.2);
}
@keyframes sp-modal-pop { from { transform: translateY(20px) scale(0.95); } to { transform: translateY(0) scale(1); } }
.sp__modal-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.sp__modal-badge {
  background: #ea580c; color: #fff; padding: 3px 12px; border-radius: 999px;
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
}
.sp__modal-day { font-size: 12px; color: #64748b; font-weight: 600; flex: 1; }
.sp__modal-title { margin: 6px 0 4px; font-size: 19px; color: #7c2d12; }
.sp__modal-desc { color: #78350f; font-size: 14px; line-height: 1.5; margin: 6px 0 10px; }
.sp__modal-notes {
  background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
  padding: 8px 12px; margin: 8px 0 12px;
}
.sp__modal-notes-head { font-size: 11px; color: #9a3412; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
.sp__modal-notes ul { padding-left: 18px; margin: 2px 0; font-size: 13px; color: #78350f; line-height: 1.5; }

@media (max-width: 768px) {
  .sp__day-grid { grid-template-columns: 1fr; }
  .sp__planning-help { grid-template-columns: 1fr; }
  .sp__summary-grid { grid-template-columns: 1fr; }
  .sp__head h1 { font-size: 17px; }
}
</style>

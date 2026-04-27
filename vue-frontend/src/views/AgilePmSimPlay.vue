<template>
  <div class="pmsim modern-ui" :class="{ 'pmsim--dead': isDead, 'pmsim--at-risk': isAtRisk }">
    <header class="pmsim__top">
      <div class="pmsim__brand">
        <span class="pmsim__logo">📡</span>
        <div>
          <div class="pmsim__title">{{ $t('agileTraining.pmSim.title') }}</div>
          <div class="pmsim__sub">
            <strong>{{ group.name || '…' }}</strong>
            <span class="pmsim__dot">•</span>
            <span>{{ $t('agileTraining.pmSim.weekOf', { w: state.current_week, total: state.total_weeks }) }}</span>
            <span class="pmsim__dot">•</span>
            <span :class="['pmsim__status', `pmsim__status--${state.status}`]">{{ statusLabel }}</span>
          </div>
        </div>
      </div>
      <div class="pmsim__lang">
        <button :class="{ act: locale==='ru' }" @click="switchLang('ru')">RU</button>
        <button :class="{ act: locale==='en' }" @click="switchLang('en')">EN</button>
      </div>
    </header>

    <!-- LOBBY: name + role -->
    <section v-if="!participantToken" class="pmsim__panel">
      <h2>{{ $t('agileTraining.pmSim.welcomeTitle') }}</h2>
      <p class="pmsim__lead">{{ $t('agileTraining.pmSim.welcomeIntro') }}</p>
      <div class="pmsim__form">
        <input v-model="displayName" :placeholder="$t('agileTraining.pmSim.yourName')" maxlength="60" />
        <button class="pmsim__btn pmsim__btn--primary" :disabled="!displayName.trim() || joining" @click="joinGroup">
          {{ $t('agileTraining.pmSim.join') }}
        </button>
      </div>
      <div class="pmsim__error" v-if="joinError">{{ joinError }}</div>
    </section>

    <section v-else-if="state.phase === 'lobby' || state.phase === 'intro'" class="pmsim__panel">
      <h2>{{ $t('agileTraining.pmSim.lobbyTitle') }}</h2>
      <p class="pmsim__lead">{{ $t('agileTraining.pmSim.welcomeIntro') }}</p>

      <h3>{{ $t('agileTraining.pmSim.pickRole') }}</h3>
      <div class="pmsim__roles">
        <button
          v-for="r in roleList"
          :key="r.key"
          :class="['pmsim__role', { 'pmsim__role--active': myRole === r.key, 'pmsim__role--taken': roleTaken(r.key) && myRole !== r.key }]"
          @click="changeRole(r.key)">
          <span class="pmsim__role-icon">{{ r.icon }}</span>
          <strong>{{ r.label }}</strong>
          <span class="pmsim__role-desc">{{ r.desc }}</span>
        </button>
      </div>

      <div class="pmsim__participants">
        <div class="pmsim__pcount">{{ $t('agileTraining.pmSim.team') }}: {{ participantsList.length }}</div>
        <ul>
          <li v-for="p in participantsList" :key="p.token">
            <span>{{ p.name }}</span>
            <span class="pmsim__pill" v-if="p.role">{{ roleLabelByKey(p.role) }}</span>
            <span v-else class="pmsim__pill pmsim__pill--ghost">—</span>
          </li>
        </ul>
      </div>

      <div class="pmsim__cta">
        <button v-if="isPO" class="pmsim__btn pmsim__btn--primary" @click="startGame">
          {{ $t('agileTraining.pmSim.startGame') }}
        </button>
        <span v-else class="pmsim__hint">{{ $t('agileTraining.pmSim.waitForPO') }}</span>
      </div>
    </section>

    <!-- PLAYING -->
    <template v-else-if="state.phase === 'playing'">
      <!-- Dashboard -->
      <section class="pmsim__dashboard">
        <div class="pmsim__metric pmsim__metric--money">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.revenue') }}</div>
          <div class="pmsim__m-value">${{ formatNumber(state.revenue_total) }}</div>
          <div class="pmsim__m-sub" v-if="state.revenue_per_week">+${{ formatNumber(state.revenue_per_week) }}/w</div>
        </div>
        <div class="pmsim__metric">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.users') }}</div>
          <div class="pmsim__m-value">{{ formatNumber(state.metrics.users) }}</div>
          <div class="pmsim__m-sub">{{ $t('agileTraining.pmSim.metric.active') }}: {{ formatNumber(state.metrics.active_users) }}</div>
        </div>
        <div class="pmsim__metric"
             :class="metricClass('satisfaction', state.metrics.satisfaction)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.satisfaction') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.satisfaction) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.satisfaction}%`"></span></div>
        </div>
        <div class="pmsim__metric" :class="metricClass('stability', state.metrics.stability)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.stability') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.stability) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.stability}%`"></span></div>
        </div>
        <div class="pmsim__metric" :class="metricClass('trust', state.metrics.trust)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.trust') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.trust) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.trust}%`"></span></div>
        </div>
        <div class="pmsim__metric pmsim__metric--debt" :class="metricClass('tech_debt', state.metrics.tech_debt, true)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.techDebt') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.tech_debt) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.tech_debt}%`"></span></div>
        </div>
        <div class="pmsim__metric">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.budget') }}</div>
          <div class="pmsim__m-value">${{ formatNumber(state.budget) }}</div>
          <div class="pmsim__m-sub">{{ $t('agileTraining.pmSim.metric.capacity') }}: {{ state.capacity_left }}/{{ 100 }}</div>
        </div>
      </section>

      <section class="pmsim__charts">
        <h3>{{ $t('agileTraining.pmSim.metricsHistory') }}</h3>
        <div class="pmsim__chart-wrap">
          <Chart :data="state.metrics_history" field="users" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.users')" color="#2563eb" />
          <Chart :data="state.metrics_history" field="revenue_total" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.revenue')" color="#059669" />
          <Chart :data="state.metrics_history" field="satisfaction" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.satisfaction')" color="#7c3aed" :max="100" />
          <Chart :data="state.metrics_history" field="stability" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.stability')" color="#0ea5e9" :max="100" />
          <Chart :data="state.metrics_history" field="trust" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.trust')" color="#f59e0b" :max="100" />
          <Chart :data="state.metrics_history" field="tech_debt" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.techDebt')" color="#dc2626" :max="100" />
        </div>
      </section>

      <!-- Risks -->
      <section class="pmsim__risks" v-if="riskBadges.length">
        <span v-for="r in riskBadges" :key="r" class="pmsim__risk">⚠ {{ r }}</span>
      </section>

      <!-- PO Quotas widget -->
      <section class="pmsim__quotas" v-if="quotaFocusList.length">
        <header class="pmsim__quotas-head">
          <h3>{{ $t('agileTraining.pmSim.quotas.title') }}</h3>
          <span class="pmsim__hint">
            {{ $t('agileTraining.pmSim.quotas.hint', {
              biz: quotaDefaults.business || 50,
              debt: quotaDefaults.tech_debt || 30,
              arch: quotaDefaults.architecture || 20,
            }) }}
          </span>
        </header>
        <div class="pmsim__quotas-grid">
          <div v-for="f in quotaFocusList" :key="f"
               :class="['pmsim__quota-card', `pmsim__quota-card--${f}`]">
            <div class="pmsim__quota-label">{{ $t('agileTraining.pmSim.quotas.labels.' + f) }}</div>
            <div class="pmsim__quota-input-row">
              <input type="number" min="0" max="100" :step="5"
                     v-model.number="quotaDraft[f]"
                     :disabled="!isPO || quotasSaving" />
              <span class="pmsim__quota-unit">%</span>
            </div>
            <div class="pmsim__quota-actual">
              <span class="pmsim__hint">{{ $t('agileTraining.pmSim.quotas.actualThisCycle') }}</span>
              <strong v-if="quotaActualPct[f] !== null" :class="quotaDeviationClass(f)">
                {{ quotaActualPct[f] }}%
                <em class="pmsim__quota-dev">
                  {{ $t('agileTraining.pmSim.quotas.deviation') }}: {{ quotaDeviationText(f) }}
                </em>
              </strong>
              <em v-else class="pmsim__hint">{{ $t('agileTraining.pmSim.quotas.noWorkYet') }}</em>
            </div>
          </div>
        </div>
        <div class="pmsim__quotas-bar" v-if="isPO">
          <span class="pmsim__hint" :class="{ 'pmsim__hint--ok': quotasSavedFlash }">
            {{ quotaDraftSum }}%
            <em v-if="quotasSavedFlash">— {{ $t('agileTraining.pmSim.quotas.saved') }}</em>
          </span>
          <button type="button" class="pmsim__btn pmsim__btn--primary"
                  :disabled="!isPO || !quotasDraftValid || quotasSaving || !quotasDirty"
                  @click="saveQuotas">
            {{ $t('agileTraining.pmSim.quotas.save') }}
          </button>
        </div>
        <div class="pmsim__tk-error" v-if="quotasError">{{ quotasError }}</div>
      </section>

      <!-- PO Toolkit -->
      <section class="pmsim__toolkit" v-if="(state.po_action_catalog || []).length">
        <header class="pmsim__toolkit-head">
          <div>
            <h3>{{ $t('agileTraining.pmSim.toolkit.title') }}</h3>
            <span class="pmsim__hint">{{ $t('agileTraining.pmSim.toolkit.hint') }}</span>
          </div>
          <div class="pmsim__po-budget">
            <span class="pmsim__po-budget-label">{{ $t('agileTraining.pmSim.toolkit.budgetTitle') }}</span>
            <strong class="pmsim__po-budget-value">
              {{ $t('agileTraining.pmSim.toolkit.budgetUsed', {
                used: state.po_actions_used_this_week || 0,
                limit: state.po_actions_per_week_limit || 2,
              }) }}
            </strong>
            <span class="pmsim__hint">
              {{ $t('agileTraining.pmSim.toolkit.budgetHint', { limit: state.po_actions_per_week_limit || 2 }) }}
            </span>
          </div>
        </header>
        <div class="pmsim__toolkit-tabs">
          <button v-for="t in toolkitCategories" :key="t.key"
                  :class="['pmsim__tk-tab', { 'pmsim__tk-tab--active': toolkitTab === t.key }]"
                  @click="toolkitTab = t.key">
            {{ t.label }} <span class="pmsim__tk-count">{{ (toolkitByCat[t.key] || []).length }}</span>
          </button>
        </div>
        <div class="pmsim__toolkit-grid">
          <article v-for="a in visibleToolkitActions" :key="a.id"
                   :class="['pmsim__tk-card', `pmsim__tk-card--${a.category}`,
                            { 'pmsim__tk-card--locked': !a.status.available,
                              'pmsim__tk-card--draft': poToolkitDraft && poToolkitDraft.id === a.id,
                              'pmsim__tk-card--selectable': isPO }]"
                   @click="selectToolkitAction(a)">
            <header class="pmsim__tk-head">
              <span class="pmsim__tk-icon" v-if="a.icon">{{ a.icon }}</span>
              <strong>{{ a.title }}</strong>
              <span v-if="a.focus" class="pmsim__focus-tag" :class="`pmsim__focus-tag--${a.focus}`">
                {{ $t('agileTraining.pmSim.toolkit.focusTag.' + a.focus) }}
              </span>
            </header>
            <p class="pmsim__tk-desc">{{ a.description }}</p>
            <ul class="pmsim__tk-effects">
              <li v-if="a.cap_cost"><span class="pmsim__fe-key">{{ $t('agileTraining.pmSim.metric.capacity') }}</span><span class="pmsim__fe-value pmsim__fe-value--bad">−{{ a.cap_cost }}</span></li>
              <li v-if="a.budget_cost"><span class="pmsim__fe-key">{{ $t('agileTraining.pmSim.metric.budget') }}</span><span class="pmsim__fe-value pmsim__fe-value--bad">−${{ formatNumber(a.budget_cost) }}</span></li>
              <li v-if="a.po_action_cost"><span class="pmsim__fe-key">{{ $t('agileTraining.pmSim.toolkit.actionCost') }}</span><span class="pmsim__fe-value pmsim__fe-value--bad">−{{ a.po_action_cost }}</span></li>
              <li v-for="(v, k) in a.effects" :key="k">
                <span class="pmsim__fe-key">{{ effectLabel(k) }}</span>
                <span class="pmsim__fe-value" :class="effectClass(v)">{{ effectValue(v) }}</span>
              </li>
            </ul>
            <footer class="pmsim__tk-foot">
              <span v-if="a.status.cooldown_left_weeks > 0" class="pmsim__pill pmsim__pill--ghost">
                ⏳ {{ $t('agileTraining.pmSim.toolkit.cooldown', { n: a.status.cooldown_left_weeks }) }}
              </span>
              <span v-else-if="a.max_per_game" class="pmsim__pill pmsim__pill--ghost">
                {{ a.status.used_count || 0 }}/{{ a.max_per_game }}
              </span>
              <span v-else-if="a.cooldown_weeks > 0" class="pmsim__pill pmsim__pill--ghost">
                {{ $t('agileTraining.pmSim.toolkit.everyN', { n: a.cooldown_weeks }) }}
              </span>
              <span v-if="!a.status.available && a.status.blocked_reasons.length"
                    class="pmsim__pill pmsim__pill--warn">
                {{ blockedReasonLabel(a.status.blocked_reasons[0]) }}
              </span>
            </footer>
          </article>
        </div>
        <div class="pmsim__toolkit-bar" v-if="isPO">
          <span v-if="poToolkitDraft" class="pmsim__tk-draft-label">
            {{ $t('agileTraining.pmSim.toolkit.selected', { name: poToolkitDraft.title }) }}
          </span>
          <div class="pmsim__toolkit-bar-btns">
            <button type="button" class="pmsim__btn pmsim__btn--ghost"
                    :disabled="!poToolkitDraft" @click="clearToolkitDraft">
              {{ $t('agileTraining.pmSim.toolkit.clear') }}
            </button>
            <button type="button" class="pmsim__btn pmsim__btn--primary"
                    :disabled="!poToolkitDraft || !poToolkitDraft.status.available || submitting"
                    @click="confirmToolkitDraft">
              {{ $t('agileTraining.pmSim.toolkit.apply') }}
            </button>
          </div>
        </div>
        <p v-if="!isPO" class="pmsim__hint">{{ $t('agileTraining.pmSim.toolkit.poOnly') }}</p>
        <div class="pmsim__tk-error" v-if="toolkitError">{{ toolkitError }}</div>
      </section>

      <!-- Event card -->
      <section v-if="state.current_event && !state.event_resolved" class="pmsim__event">
        <header>
          <span class="pmsim__event-type">{{ eventTypeLabel(state.current_event.type) }}</span>
          <h2>{{ state.current_event.title }}</h2>
        </header>
        <p class="pmsim__event-desc">{{ state.current_event.description }}</p>

        <div class="pmsim__options">
          <article
            v-for="opt in state.current_event.options"
            :key="opt.id"
            :class="['pmsim__option', { 'pmsim__option--mine': myEventVote === opt.id, 'pmsim__option--leading': leadingEventOption === opt.id && eventVotesTotal > 0 }]">
            <div class="pmsim__option-head">
              <strong>{{ opt.title }}</strong>
              <span class="pmsim__votes">{{ (state.votes.event && state.votes.event[opt.id]) || 0 }}</span>
            </div>
            <p>{{ opt.description }}</p>
            <button class="pmsim__btn pmsim__btn--ghost" @click="voteEvent(opt.id)">
              {{ myEventVote === opt.id ? $t('agileTraining.pmSim.voted') : $t('agileTraining.pmSim.vote') }}
            </button>
          </article>
        </div>

        <div class="pmsim__decision-bar">
          <span>{{ $t('agileTraining.pmSim.poDecision') }}</span>
          <select v-model="poDecision" :disabled="!isPO">
            <option value="">— {{ $t('agileTraining.pmSim.pickOption') }} —</option>
            <option v-for="opt in state.current_event.options" :key="opt.id" :value="opt.id">{{ opt.title }}</option>
          </select>
          <button class="pmsim__btn pmsim__btn--primary" :disabled="!isPO || !poDecision || submitting" @click="confirmEventDecision">
            {{ $t('agileTraining.pmSim.confirmDecision') }}
          </button>
        </div>
        <div v-if="!isPO" class="pmsim__hint">{{ $t('agileTraining.pmSim.poConfirmsHint') }}</div>
      </section>

      <!-- Feature window -->
      <section v-if="state.feature_choice_open" class="pmsim__features">
        <h2>{{ $t('agileTraining.pmSim.featureCycleTitle', { c: state.cycle_index }) }}</h2>
        <p class="pmsim__hint">{{ $t('agileTraining.pmSim.featureRules') }}</p>
        <div class="pmsim__pick-help" v-if="featurePickHelp">
          <span>{{ featurePickHelp }}</span>
        </div>
        <p class="pmsim__capacity-line">
          {{ $t('agileTraining.pmSim.metric.capacity') }}: <strong>{{ state.capacity_left }}</strong>
          <span v-if="featureCapacityUsed > 0"> · {{ $t('agileTraining.pmSim.using') }}: {{ featureCapacityUsed }}</span>
          <span v-if="featureCapacityUsed > 0"
                class="pmsim__risk-pill"
                :class="deliveryRiskClass"
                :title="$t('agileTraining.pmSim.riskHelp')">
            ⏱ {{ $t('agileTraining.pmSim.slipRisk') }}: {{ Math.round(deliveryRiskPct) }}%
          </span>
        </p>
        <p v-if="(pendingReleases || []).length" class="pmsim__pending-line">
          ⌛ {{ $t('agileTraining.pmSim.carryFromPrev') }}:
          <span v-for="(p, i) in pendingReleases" :key="p.key + p.started_week">
            <strong>{{ p.title }}</strong> ({{ p.capacity }} cap, {{ $t('agileTraining.pmSim.dueCycle', { c: p.delivery_cycle }) }}){{ i < pendingReleases.length - 1 ? ', ' : '' }}
          </span>
        </p>
        <div class="pmsim__feature-grid">
          <article
            v-for="f in state.feature_options"
            :key="String(f.key)"
            :class="['pmsim__feature',
                     { 'pmsim__feature--picked': featurePicksStr.includes(String(f.key)),
                       'pmsim__feature--big': Number(f.capacity) >= 40 && String(f.key) !== 'stabilize',
                       'pmsim__feature--stabilize': String(f.key) === 'stabilize' }]"
            @click="toggleFeaturePick(f)">
            <header>
              <strong>{{ f.title }}</strong>
              <span class="pmsim__feat-cap">{{ f.capacity }} cap</span>
            </header>
            <div class="pmsim__feat-tags">
              <span v-if="f.focus" class="pmsim__focus-tag" :class="`pmsim__focus-tag--${f.focus}`">
                {{ $t('agileTraining.pmSim.toolkit.focusTag.' + f.focus) }}
              </span>
              <span v-if="String(f.key) === 'stabilize'" class="pmsim__pick-badge pmsim__pick-badge--solo">
                {{ $t('agileTraining.pmSim.feat.solo') }}
              </span>
              <span v-else-if="Number(f.capacity) >= 40" class="pmsim__pick-badge pmsim__pick-badge--big">
                {{ $t('agileTraining.pmSim.feat.big') }}
              </span>
              <span v-else class="pmsim__pick-badge pmsim__pick-badge--small">
                {{ $t('agileTraining.pmSim.feat.small') }}
              </span>
            </div>
            <p>{{ f.description }}</p>
            <ul class="pmsim__feat-effects">
              <li v-for="(v,k) in f.effects" :key="k">
                <span class="pmsim__fe-key">{{ effectLabel(k) }}</span>
                <span class="pmsim__fe-value" :class="effectClass(v)">{{ effectValue(v) }}</span>
              </li>
            </ul>
            <div class="pmsim__feat-pick" v-if="featurePicksStr.includes(String(f.key))">✓ {{ $t('agileTraining.pmSim.picked') }}</div>
            <div class="pmsim__votes-row" @click.stop>
              <span class="pmsim__pill">{{ $t('agileTraining.pmSim.votes') }}: {{ (state.votes.feature && state.votes.feature[f.key]) || 0 }}</span>
              <button class="pmsim__btn pmsim__btn--ghost" @click="voteFeature(f.key)">
                {{ myFeatureVote === f.key ? $t('agileTraining.pmSim.voted') : $t('agileTraining.pmSim.vote') }}
              </button>
            </div>
          </article>
        </div>
        <div class="pmsim__decision-bar">
          <button class="pmsim__btn pmsim__btn--primary"
                  :disabled="!isPO || !canConfirmFeatures || submitting"
                  @click="confirmFeatureRelease">
            {{ $t('agileTraining.pmSim.releaseFeatures') }}
          </button>
          <button class="pmsim__btn pmsim__btn--ghost" :disabled="!isPO" @click="confirmFeatureRelease(true)">
            {{ $t('agileTraining.pmSim.skipFeatures') }}
          </button>
        </div>
      </section>

      <!-- Released features -->
      <section v-if="(state.feature_releases || []).length" class="pmsim__released">
        <h3>{{ $t('agileTraining.pmSim.released') }}</h3>
        <div class="pmsim__released-list">
          <span v-for="r in state.feature_releases" :key="r.key + r.week"
                class="pmsim__released-pill"
                :class="{ 'pmsim__released-pill--late': r.slipped }">
            <strong>w{{ r.week }}:</strong> {{ r.title }}
            <em v-if="r.slipped" class="pmsim__late-tag">⏱ {{ $t('agileTraining.pmSim.deliveredLate') }}</em>
          </span>
        </div>
      </section>

      <!-- Last consequences -->
      <section v-if="lastConsequencesParts.length || state.consequences_text" class="pmsim__consequences">
        <strong>{{ $t('agileTraining.pmSim.lastConsequences') }}:</strong>
        <span v-if="lastConsequencesParts.length" class="pmsim__cons-list">
          <span v-for="(p, i) in lastConsequencesParts" :key="i"
                class="pmsim__cons-pill"
                :class="p.delta > 0 ? 'pmsim__cons-pill--up' : (p.delta < 0 ? 'pmsim__cons-pill--down' : '')">
            {{ p.label }} {{ p.delta > 0 ? '+' : '' }}{{ p.delta }}
          </span>
        </span>
        <span v-else>{{ state.consequences_text }}</span>
      </section>

      <!-- AI helper -->
      <section class="pmsim__ai">
        <h3>{{ $t('agileTraining.pmSim.aiCoach') }}</h3>
        <p class="pmsim__hint">{{ $t('agileTraining.pmSim.aiHint') }}</p>
        <textarea v-model="aiInput" rows="2" :placeholder="$t('agileTraining.pmSim.aiHint')"></textarea>
        <div class="pmsim__ai-row">
          <button class="pmsim__btn pmsim__btn--ghost"
                  :disabled="aiBusy || aiCallsLeft<=0"
                  :title="$t('agileTraining.pmSim.aiTradeoffHint')"
                  @click="askAi('tradeoff')">
            {{ $t('agileTraining.pmSim.aiTradeoff') }}
          </button>
          <button class="pmsim__btn pmsim__btn--ghost"
                  :disabled="aiBusy || aiCallsLeft<=0"
                  :title="$t('agileTraining.pmSim.aiUserVoiceHint')"
                  @click="askAi('userVoice')">
            {{ $t('agileTraining.pmSim.aiUserVoice') }}
          </button>
          <button class="pmsim__btn pmsim__btn--ghost"
                  :disabled="aiBusy || aiCallsLeft<=0"
                  :title="$t('agileTraining.pmSim.aiExplainHint')"
                  @click="askAi('explain')">
            {{ $t('agileTraining.pmSim.aiExplain') }}
          </button>
          <span class="pmsim__ai-counter">{{ aiCallsLeft }}/{{ state.my && state.my.ai_calls_limit }}</span>
        </div>
        <pre class="pmsim__ai-reply" v-if="aiReply">{{ aiReply }}</pre>
      </section>

      <!-- History -->
      <section class="pmsim__history" v-if="(state.history || []).length">
        <h3>{{ $t('agileTraining.pmSim.history') }}</h3>
        <ol>
          <li v-for="(h,i) in [...state.history].reverse()" :key="i">
            <strong>w{{ h.week }}</strong>
            <template v-if="h.kind === 'event'">
              · {{ h.event.title }} → <em>{{ h.option.title }}</em>
              <span class="pmsim__history-effects" v-if="h.consequences && h.consequences.length">— {{ h.consequences.join(', ') }}</span>
            </template>
            <template v-else-if="h.kind === 'feature'">
              · 🚀
              <span v-for="(rel, ri) in (h.released || [])" :key="rel.key + ri">
                {{ rel.title }}<em v-if="rel.slipped" class="pmsim__late-tag pmsim__late-tag--mini">⏱ {{ $t('agileTraining.pmSim.slipped') }}</em>{{ ri < (h.released || []).length - 1 ? ', ' : '' }}
              </span>
              <span v-if="!(h.released || []).length">{{ $t('agileTraining.pmSim.skipped') }}</span>
            </template>
            <template v-else-if="h.kind === 'delivery'">
              · 📦 {{ $t('agileTraining.pmSim.lateDeliveryHistory') }}:
              {{ (h.delivered || []).map(r => r.title).join(', ') }}
            </template>
          </li>
        </ol>
      </section>

      <!-- Leaderboard hint -->
      <section v-if="state.leaderboard_unlocked_weeks && state.leaderboard_unlocked_weeks.length" class="pmsim__leader-hint">
        <strong>{{ $t('agileTraining.pmSim.leaderboardOpened') }}:</strong>
        {{ state.leaderboard_unlocked_weeks.map(w => 'w'+w).join(', ') }}
      </section>
    </template>

    <!-- FINISHED -->
    <section v-else-if="state.phase === 'finished'" class="pmsim__final" id="pmsim-final">
      <h2>{{ isDead ? $t('agileTraining.pmSim.gameOver') : $t('agileTraining.pmSim.finalTitle') }}</h2>
      <div class="pmsim__final-summary">
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.metric.revenue') }}</div>
          <div class="pmsim__final-value">${{ formatNumber(state.revenue_total) }}</div>
        </div>
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.metric.users') }}</div>
          <div class="pmsim__final-value">{{ formatNumber(state.metrics.users) }}</div>
        </div>
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.status') }}</div>
          <div :class="['pmsim__final-value', `pmsim__status--${state.status}`]">{{ statusLabel }}</div>
          <div class="pmsim__hint" v-if="state.death_reason">{{ state.death_reason }}</div>
        </div>
      </div>

      <div class="pmsim__chart-wrap">
        <Chart :data="state.metrics_history" field="revenue_total" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.revenue')" color="#059669" />
        <Chart :data="state.metrics_history" field="users" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.users')" color="#2563eb" />
        <Chart :data="state.metrics_history" field="satisfaction" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.satisfaction')" color="#7c3aed" :max="100" />
        <Chart :data="state.metrics_history" field="trust" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.trust')" color="#f59e0b" :max="100" />
      </div>

      <div class="pmsim__final-events">
        <h3>{{ $t('agileTraining.pmSim.allDecisions') }}</h3>
        <ol>
          <li v-for="(h,i) in state.history" :key="i">
            <strong>w{{ h.week }}</strong>
            <template v-if="h.kind === 'event'"> · {{ h.event.title }} → <em>{{ h.option.title }}</em></template>
            <template v-else-if="h.kind === 'feature'"> · 🚀
              <span v-for="(rel, ri) in (h.released || [])" :key="rel.key + ri">
                {{ rel.title }}<em v-if="rel.slipped" class="pmsim__late-tag pmsim__late-tag--mini">⏱ {{ $t('agileTraining.pmSim.slipped') }}</em>{{ ri < (h.released || []).length - 1 ? ', ' : '' }}
              </span>
              <span v-if="!(h.released || []).length">{{ $t('agileTraining.pmSim.skipped') }}</span>
            </template>
            <template v-else-if="h.kind === 'delivery'"> · 📦 {{ $t('agileTraining.pmSim.lateDeliveryHistory') }}: {{ (h.delivered || []).map(r => r.title).join(', ') }}</template>
          </li>
        </ol>
      </div>

      <div class="pmsim__cta">
        <button class="pmsim__btn pmsim__btn--primary" @click="printReport">🖨 {{ $t('agileTraining.pmSim.exportPdf') }}</button>
      </div>
    </section>

    <!-- Weekly Recap modal -->
    <div class="pmsim__recap-overlay" v-if="recapToShow" @click.self="closeRecap">
      <div class="pmsim__recap" role="dialog" aria-modal="true">
        <header class="pmsim__recap-head">
          <h3>{{ $t('agileTraining.pmSim.recap.title', { w: recapToShow.week }) }}</h3>
          <button class="pmsim__recap-x" @click="closeRecap" aria-label="Close">×</button>
        </header>
        <p class="pmsim__recap-lead">
          {{ $t('agileTraining.pmSim.recap.lead', { next: recapToShow.next_week }) }}
        </p>

        <div class="pmsim__recap-section" v-if="recapToShow.event">
          <h4>{{ $t('agileTraining.pmSim.recap.eventTitle') }}</h4>
          <p>
            <strong>{{ recapToShow.event.title }}</strong>
            <em v-if="recapToShow.decision"> → {{ recapToShow.decision.title }}</em>
          </p>
          <div v-if="recapDecisionStructParts.length" class="pmsim__cons-list">
            <span v-for="(p, i) in recapDecisionStructParts" :key="i"
                  class="pmsim__cons-pill"
                  :class="p.delta > 0 ? 'pmsim__cons-pill--up' : (p.delta < 0 ? 'pmsim__cons-pill--down' : '')">
              {{ p.label }} {{ p.delta > 0 ? '+' : '' }}{{ p.delta }}
            </span>
          </div>
          <p class="pmsim__hint" v-else-if="(recapToShow.decision_notes || []).length">
            {{ recapToShow.decision_notes.join(', ') }}
          </p>
        </div>

        <div class="pmsim__recap-section" v-if="(recapToShow.released_features || []).length">
          <h4>{{ $t('agileTraining.pmSim.recap.releasedTitle') }}</h4>
          <ul>
            <li v-for="(rel, ri) in recapToShow.released_features" :key="rel.key + ri">
              {{ rel.title }}
              <em class="pmsim__late-tag pmsim__late-tag--mini" v-if="rel.slipped">
                ⏱ {{ $t('agileTraining.pmSim.slipped') }}
              </em>
            </li>
          </ul>
        </div>

        <div class="pmsim__recap-section" v-if="(recapToShow.late_deliveries || []).length">
          <h4>📦 {{ $t('agileTraining.pmSim.recap.lateDeliveriesTitle') }}</h4>
          <ul>
            <li v-for="(rel, ri) in recapToShow.late_deliveries" :key="'late-' + ri">
              {{ rel.title }}
              <span v-if="(rel.notes || []).length" class="pmsim__hint">— {{ rel.notes.join(', ') }}</span>
            </li>
          </ul>
        </div>

        <div class="pmsim__recap-section" v-if="(recapToShow.scrum_penalty || []).length">
          <h4>⚠ {{ $t('agileTraining.pmSim.recap.scrumPenaltyTitle') }}</h4>
          <ul class="pmsim__recap-scrum-list">
            <li v-for="(sp, si) in recapToShow.scrum_penalty" :key="si + (sp.narrative_key || sp.reason)">
              <p class="pmsim__hint">{{ scrumPenaltyNarrative(sp) }}</p>
            </li>
          </ul>
        </div>

        <div class="pmsim__recap-section" v-if="recapDeltas.length">
          <h4>{{ $t('agileTraining.pmSim.recap.metricsTitle') }}</h4>
          <ul class="pmsim__recap-deltas">
            <li v-for="d in recapDeltas" :key="d.key" :class="['pmsim__recap-delta', d.delta > 0 ? 'pmsim__recap-delta--up' : 'pmsim__recap-delta--down']">
              <span class="pmsim__recap-key">{{ effectLabel(d.key) }}</span>
              <span class="pmsim__recap-vals">
                <span class="pmsim__recap-before">{{ d.before }}</span>
                →
                <span class="pmsim__recap-after">{{ d.after }}</span>
                <em>({{ d.delta > 0 ? '+' : '' }}{{ d.delta }})</em>
              </span>
            </li>
          </ul>
        </div>

        <div class="pmsim__recap-section" v-if="recapQuotaReport">
          <h4>📐 {{ $t('agileTraining.pmSim.recap.quotaTitle') }}</h4>
          <ul class="pmsim__recap-quota-list">
            <li v-for="f in quotaFocusList" :key="f">
              <strong>{{ $t('agileTraining.pmSim.quotas.labels.' + f) }}</strong>:
              {{ recapQuotaReport.actual_pct[f] || 0 }}% / {{ recapQuotaReport.quotas[f] || 0 }}%
              <em :class="recapQuotaReport.deviations && Math.abs(recapQuotaReport.deviations[f] || 0) > 22 ? 'pmsim__cons-pill--down' : ''">
                ({{ (recapQuotaReport.deviations[f] || 0) > 0 ? '+' : '' }}{{ recapQuotaReport.deviations[f] || 0 }} pp)
              </em>
            </li>
          </ul>
          <p class="pmsim__hint">{{ recapQuotaText }}</p>
        </div>

        <div class="pmsim__recap-section pmsim__recap-focus" v-if="recapToShow.focus">
          <h4>🎯 {{ $t('agileTraining.pmSim.recap.focusTitle', { w: recapToShow.next_week }) }}</h4>
          <p>{{ recapFocusText }}</p>
        </div>

        <footer class="pmsim__recap-foot">
          <button class="pmsim__btn pmsim__btn--primary" @click="closeRecap">
            {{ $t('agileTraining.pmSim.recap.continue') }}
          </button>
        </footer>
      </div>
    </div>

    <div v-if="loading" class="pmsim__loading">{{ $t('agileTraining.pmSim.loading') }}</div>
    <div v-if="loadError" class="pmsim__error">{{ loadError }}</div>
  </div>
</template>

<script>
import axios from 'axios';
import Chart from '@/components/PmSimChart.vue';

const TOKEN_KEY_PREFIX = 'pmsim:token:';
const NAME_KEY_PREFIX = 'pmsim:name:';
const POLL_INTERVAL_MS = 4000;

function read(prefix, slug) {
  try { return localStorage.getItem(prefix + slug) || ''; } catch (_) { return ''; }
}
function write(prefix, slug, val) {
  try { localStorage.setItem(prefix + slug, val || ''); } catch (_) { /* noop */ }
}

export default {
  name: 'AgilePmSimPlay',
  components: { Chart },
  props: { slug: { type: String, required: true } },
  data() {
    return {
      group: {}, sessionInfo: {},
      state: {
        phase: 'lobby', current_week: 0, total_weeks: 20, cycle_index: 1, status: 'alive',
        metrics: { users: 0, active_users: 0, satisfaction: 0, stability: 0, tech_debt: 0, trust: 0 },
        revenue_total: 0, revenue_per_week: 0, budget: 0, capacity_left: 0,
        feature_choice_open: false, feature_options: [], feature_releases: [],
        history: [], metrics_history: [], votes: { event: {}, feature: {} },
        my_vote: { event: null, feature: null },
        leaderboard_unlocked_weeks: [], current_event: null, event_resolved: true,
        my: null,
      },
      lastVersion: -1,
      participantToken: '',
      displayName: '',
      joining: false, joinError: '',
      loading: true, loadError: '',
      submitting: false,
      poDecision: '',
      featurePicks: [],
      aiInput: '', aiReply: '', aiBusy: false,
      pollTimer: null,
      locale: this.$i18n.locale,
      toolkitTab: 'discovery',
      toolkitError: '',
      poToolkitDraft: null,
      recapDismissedWeek: -1,
      recapForceShow: null,
      quotaDraft: { business: 50, tech_debt: 30, architecture: 20 },
      quotasSaving: false,
      quotasError: '',
      quotasSavedFlash: false,
    };
  },
  computed: {
    featurePicksStr() {
      return (this.featurePicks || []).map((k) => String(k));
    },
    isPO() { return !!(this.state.my && this.state.my.is_po); },
    myRole() { return (this.state.my && this.state.my.role) || ''; },
    myEventVote() { return this.state.my_vote && this.state.my_vote.event; },
    myFeatureVote() { return this.state.my_vote && this.state.my_vote.feature; },
    isDead() { return this.state.status === 'dead'; },
    isAtRisk() { return this.state.status === 'at_risk'; },
    statusLabel() {
      const k = this.state.status || 'alive';
      return this.$t(`agileTraining.pmSim.statusLabel.${k}`);
    },
    eventVotesTotal() {
      const v = this.state.votes && this.state.votes.event || {};
      return Object.values(v).reduce((a, b) => a + (Number(b) || 0), 0);
    },
    leadingEventOption() {
      const v = this.state.votes && this.state.votes.event || {};
      let best = null, max = -1;
      Object.keys(v).forEach((k) => { if (v[k] > max) { max = v[k]; best = k; } });
      return best;
    },
    aiCallsLeft() {
      const my = this.state.my;
      if (!my) return 0;
      return Math.max(0, (my.ai_calls_limit || 0) - (my.ai_calls || 0));
    },
    roleList() {
      return [
        { key: 'po', icon: '👑', label: this.$t('agileTraining.pmSim.roleLabel.po'), desc: this.$t('agileTraining.pmSim.roleDesc.po') },
        { key: 'analyst', icon: '📊', label: this.$t('agileTraining.pmSim.roleLabel.analyst'), desc: this.$t('agileTraining.pmSim.roleDesc.analyst') },
        { key: 'tech', icon: '🛠', label: this.$t('agileTraining.pmSim.roleLabel.tech'), desc: this.$t('agileTraining.pmSim.roleDesc.tech') },
        { key: 'growth', icon: '🚀', label: this.$t('agileTraining.pmSim.roleLabel.growth'), desc: this.$t('agileTraining.pmSim.roleDesc.growth') },
        { key: 'advocate', icon: '💚', label: this.$t('agileTraining.pmSim.roleLabel.advocate'), desc: this.$t('agileTraining.pmSim.roleDesc.advocate') },
      ];
    },
    participantsList() {
      const map = this.state.participants || {};
      return Object.keys(map).map((tk) => ({ token: tk, name: map[tk].name || '…', role: map[tk].role }));
    },
    riskBadges() {
      const r = [];
      const m = this.state.metrics || {};
      if (m.users && m.users < 4000) r.push(this.$t('agileTraining.pmSim.risk.users'));
      if (m.satisfaction < 40) r.push(this.$t('agileTraining.pmSim.risk.satisfaction'));
      if (m.stability < 40) r.push(this.$t('agileTraining.pmSim.risk.stability'));
      if (m.trust < 40) r.push(this.$t('agileTraining.pmSim.risk.trust'));
      if (m.tech_debt > 80) r.push(this.$t('agileTraining.pmSim.risk.techDebt'));
      if (this.state.monetization_on && this.state.revenue_per_week === 0) r.push(this.$t('agileTraining.pmSim.risk.noRevenue'));
      return r;
    },
    featureCapacityUsed() {
      const map = {};
      (this.state.feature_options || []).forEach((f) => { map[String(f.key)] = f.capacity; });
      return (this.featurePicks || []).reduce((sum, k) => sum + (Number(map[String(k)]) || 0), 0);
    },
    pickedHasStabilize() {
      return (this.featurePicks || []).some((k) => String(k) === 'stabilize');
    },
    pickedBigCount() {
      return (this.featurePicks || []).filter((k) => {
        const f = (this.state.feature_options || []).find((x) => String(x.key) === String(k));
        return f && (f.capacity || 0) >= 40;
      }).length;
    },
    canConfirmFeatures() {
      if (!this.featurePicks.length) return false;
      if (this.featureCapacityUsed > this.state.capacity_left) return false;
      if (this.featurePicks.length > 2) return false;
      if (this.pickedBigCount > 1) return false;
      if (this.pickedBigCount === 1 && this.featurePicks.length > 1) return false;
      if (this.pickedHasStabilize && this.featurePicks.length > 1) return false;
      return true;
    },
    pendingReleases() {
      return this.state.pending_releases || [];
    },
    deliveryRiskPct() {
      // Зеркалит формулу с бэкенда: учитываем capacity-утилизацию,
      // tech_debt и stability. Возвращаем 0..max_pct.
      const factors = this.state.risk_factors;
      if (!factors) return 0;
      const total = this.featureCapacityUsed;
      if (total <= 0) return 0;
      const cap = Math.max(1, factors.capacity_per_cycle || 100);
      const util = (total / cap) * 100;
      const base = Math.max(0, util - (factors.threshold_pct || 60)) * (factors.slope || 1.5);
      const m = this.state.metrics || {};
      const debt = Number(m.tech_debt) || 0;
      const stab = Number(m.stability) || 0;
      const debtAdj = Math.max(0, debt - (factors.debt_neutral || 40)) * (factors.debt_slope || 0.4);
      const stabAdj = Math.max(0, (factors.stab_neutral || 70) - stab) * (factors.stab_slope || 0.3);
      const max = factors.max_pct || 60;
      return Math.max(0, Math.min(max, base + debtAdj + stabAdj));
    },
    deliveryRiskClass() {
      const r = this.deliveryRiskPct;
      if (r <= 0) return 'pmsim__risk-pill--ok';
      if (r < 15) return 'pmsim__risk-pill--low';
      if (r < 35) return 'pmsim__risk-pill--med';
      return 'pmsim__risk-pill--high';
    },
    toolkitCategories() {
      return [
        { key: 'discovery',   label: this.$t('agileTraining.pmSim.toolkit.cat.discovery') },
        { key: 'business',    label: this.$t('agileTraining.pmSim.toolkit.cat.business') },
        { key: 'engineering', label: this.$t('agileTraining.pmSim.toolkit.cat.engineering') },
        { key: 'growth',      label: this.$t('agileTraining.pmSim.toolkit.cat.growth') },
        { key: 'pivot',       label: this.$t('agileTraining.pmSim.toolkit.cat.pivot') },
        { key: 'scrum',       label: this.$t('agileTraining.pmSim.toolkit.cat.scrum') },
      ];
    },
    toolkitByCat() {
      const list = this.state.po_action_catalog || [];
      const out = { discovery: [], business: [], engineering: [], growth: [], pivot: [], scrum: [] };
      list.forEach((a) => {
        const cat = a.category || 'discovery';
        if (out[cat]) out[cat].push(a);
        else out.discovery.push(a);
      });
      return out;
    },
    visibleToolkitActions() {
      return this.toolkitByCat[this.toolkitTab] || [];
    },
    quotaFocusList() {
      return this.state.quota_focuses || ['business', 'tech_debt', 'architecture'];
    },
    quotaDefaults() {
      return this.state.quota_defaults || { business: 50, tech_debt: 30, architecture: 20 };
    },
    quotaActualPct() {
      const load = this.state.cycle_focus_load || {};
      let total = 0;
      this.quotaFocusList.forEach((f) => { total += Number(load[f]) || 0; });
      const out = {};
      this.quotaFocusList.forEach((f) => {
        if (total <= 0) { out[f] = null; return; }
        out[f] = Math.round(((Number(load[f]) || 0) / total) * 100);
      });
      return out;
    },
    quotaDraftSum() {
      return this.quotaFocusList.reduce((s, f) => s + (Number(this.quotaDraft[f]) || 0), 0);
    },
    quotasDraftValid() {
      if (this.quotaDraftSum !== 100) return false;
      return this.quotaFocusList.every((f) => {
        const v = Number(this.quotaDraft[f]);
        return Number.isFinite(v) && v >= 0 && v <= 100;
      });
    },
    quotasDirty() {
      const cur = this.state.quotas || {};
      return this.quotaFocusList.some((f) => Number(cur[f] || 0) !== Number(this.quotaDraft[f] || 0));
    },
    lastConsequencesParts() {
      const arr = this.state.consequences_struct || [];
      return this.localizeConsequenceStruct(arr);
    },
    recapDecisionStructParts() {
      const r = this.recapToShow;
      if (!r) return [];
      const arr = r.decision_notes_struct || [];
      return this.localizeConsequenceStruct(arr);
    },
    recapQuotaReport() {
      const r = this.recapToShow;
      if (!r || !r.quota_report) return null;
      return r.quota_report;
    },
    recapQuotaText() {
      const r = this.recapQuotaReport;
      if (!r) return '';
      const dev = r.max_deviation || 0;
      const tol = (this.state.quota_tolerance_pct != null) ? this.state.quota_tolerance_pct : 18;
      const heavy = 22;
      if (dev <= tol) return this.$t('agileTraining.pmSim.recap.quotaBalanced');
      if (dev >= heavy) return this.$t('agileTraining.pmSim.recap.quotaPenalty');
      return this.$t('agileTraining.pmSim.recap.quotaOk');
    },
    featurePickHelp() {
      const t = (k, v) => this.$t(`agileTraining.pmSim.feat.${k}`, v || {});
      if (!this.featurePicks.length) return t('helpEmpty');
      if (this.pickedHasStabilize) return t('helpStabilize');
      if (this.pickedBigCount === 1) return t('helpBig');
      if (this.featurePicks.length === 2) return t('helpTwo');
      if (this.featurePicks.length === 1) return t('helpOneSmall');
      return '';
    },
    latestBackendRecap() {
      const arr = this.state.weekly_recaps || [];
      return arr.length ? arr[arr.length - 1] : null;
    },
    recapToShow() {
      if (this.recapForceShow) return this.recapForceShow;
      const r = this.latestBackendRecap;
      if (!r) return null;
      if (this.recapDismissedWeek === r.week) return null;
      // Не показываем recap пользователю до того, как он стал участником
      if (!this.participantToken) return null;
      // Не показываем сразу: подождём, пока хотя бы /state получили
      if (this.state.phase === 'lobby') return null;
      return r;
    },
    recapDeltas() {
      const r = this.recapToShow;
      if (!r || !r.deltas) return [];
      const order = ['users', 'active_users', 'satisfaction', 'stability', 'tech_debt', 'trust', 'capacity_left', 'budget', 'revenue_total', 'revenue_per_week'];
      const out = [];
      order.forEach((k) => {
        const d = r.deltas[k];
        if (d && d.delta !== 0) out.push({ key: k, before: d.before, after: d.after, delta: d.delta });
      });
      return out;
    },
    recapFocusText() {
      const r = this.recapToShow;
      if (!r || !r.focus) return '';
      const key = r.focus.key || 'balanced';
      return this.$t(`agileTraining.pmSim.recap.focus.${key}`);
    },
  },
  watch: {
    '$i18n.locale'(val) { if (val !== this.locale) { this.locale = val; this.loadState(true).catch(()=>{}); } },
    'state.feature_choice_open'(val) { if (!val) this.featurePicks = []; },
    'state.quotas': {
      deep: true,
      handler(val) { this.syncQuotaDraft(val); },
    },
  },
  async mounted() {
    this.participantToken = read(TOKEN_KEY_PREFIX, this.slug);
    this.displayName = read(NAME_KEY_PREFIX, this.slug);
    try { await this.loadState(true); }
    catch (e) { this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error'; }
    finally { this.loading = false; }
    this.syncQuotaDraft(this.state.quotas);
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
      this.pollTimer = setInterval(() => this.loadState(false).catch(()=>{}), POLL_INTERVAL_MS);
    },
    stopPolling() { if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; } },
    formatNumber(n) {
      if (n === undefined || n === null) return '0';
      const k = Math.abs(n);
      if (k >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
      if (k >= 1_000) return (n / 1_000).toFixed(k >= 10_000 ? 0 : 1).replace('.0', '') + 'k';
      return String(Math.round(n));
    },
    metricClass(_key, value, inverted) {
      const v = Number(value) || 0;
      const bad = inverted ? v >= 80 : v <= 30;
      const warn = inverted ? v >= 60 : v <= 50;
      if (bad) return 'pmsim__metric--bad';
      if (warn) return 'pmsim__metric--warn';
      return 'pmsim__metric--ok';
    },
    eventTypeLabel(type) {
      return this.$t(`agileTraining.pmSim.eventType.${type || 'user'}`);
    },
    roleLabelByKey(k) { return this.$t(`agileTraining.pmSim.roleLabel.${k || 'analyst'}`); },
    roleTaken(k) {
      return Object.values(this.state.roles || {}).includes(k);
    },
    effectLabel(k) {
      const kk = String(k);
      const path = `agileTraining.pmSim.metricKey.${kk}`;
      if (this.$te && this.$te(path)) return this.$t(path);
      const map = {
        users: 'users', users_pct: 'users %', active_users: 'active', active_users_pct: 'active %',
        satisfaction: 'sat', stability: 'stab', tech_debt: 'tech debt', trust: 'trust',
        churn_bump: 'churn', growth_pct: 'growth %', capacity_delta: 'capacity', budget_delta: 'budget',
        revenue_per_week: 'revenue/w', revenue_potential: 'revenue', monetization_on: 'monetize',
        ad_strength: 'ads', tech_debt_delta: 'tech debt', investor_pressure_delta: 'investor pressure',
        first_week_satisfaction_dip: 'sat dip',
        capacity_left: 'capacity', budget: 'budget', revenue_total: 'revenue',
      };
      return map[kk] || kk;
    },
    effectClass(v) {
      if (typeof v === 'boolean') return '';
      const num = Number(v);
      if (Number.isFinite(num)) {
        if (num > 0) return 'pmsim__fe--up';
        if (num < 0) return 'pmsim__fe--down';
      }
      return '';
    },
    effectValue(v) {
      if (typeof v === 'boolean') return v ? 'on' : 'off';
      const num = Number(v);
      if (Number.isFinite(num)) return (num > 0 ? '+' : '') + num;
      return String(v);
    },
    async loadState(updateLocal) {
      const params = { locale: this.locale };
      if (this.participantToken) params.participant_token = this.participantToken;
      const res = await axios.get(`/api/agile-training/pm-sim/g/${this.slug}/state`, { params });
      this.group = res.data.group || {};
      this.sessionInfo = res.data.session || {};
      const s = res.data.state;
      if (s) {
        if (!updateLocal && this.state && s.version === this.lastVersion) return;
        this.state = s;
        this.lastVersion = s.version;
      }
    },
    async joinGroup() {
      this.joining = true; this.joinError = '';
      try {
        const body = { display_name: this.displayName || undefined };
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, body);
        this.participantToken = res.data.participant_token;
        write(TOKEN_KEY_PREFIX, this.slug, this.participantToken);
        write(NAME_KEY_PREFIX, this.slug, this.displayName);
        await this.loadState(true);
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.joining = false; }
    },
    async changeRole(role) {
      if (!this.participantToken) return;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/join`, {
          participant_token: this.participantToken, role: role || null,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async startGame() {
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/start`, {
          participant_token: this.participantToken,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async voteEvent(optionId) {
      const same = this.myEventVote === optionId;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/vote`, {
          participant_token: this.participantToken, kind: 'event', choice: same ? '' : optionId,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async voteFeature(key) {
      const same = this.myFeatureVote === key;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/vote`, {
          participant_token: this.participantToken, kind: 'feature', choice: same ? '' : key,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async confirmEventDecision() {
      if (!this.poDecision) return;
      this.submitting = true;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/event/decide`, {
          participant_token: this.participantToken, option_id: this.poDecision,
        });
        this.poDecision = '';
        await this.loadState(true);
      } catch (e) {
        this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.submitting = false; }
    },
    featMeta(key) {
      const k = String(key);
      const row = (this.state.feature_options || []).find((x) => String(x.key) === k);
      const cap = Number((row && row.capacity) != null ? row.capacity : 0);
      return { key: k, cap, isBig: cap >= 40, isStabilize: k === 'stabilize' };
    },
    toggleFeaturePick(f) {
      const m = this.featMeta(f.key);
      const key = m.key;
      let n = (this.featurePicks || []).map((x) => String(x));
      const i = n.indexOf(key);
      if (i >= 0) {
        n.splice(i, 1);
        this.featurePicks = n;
        return;
      }
      if (m.isStabilize) {
        this.featurePicks = [key];
        return;
      }
      if (m.isBig) {
        this.featurePicks = [key];
        return;
      }
      const onlySmall = n.filter((k) => {
        const e = this.featMeta(k);
        return !e.isStabilize && !e.isBig;
      });
      if (onlySmall.length === 0) {
        this.featurePicks = [key];
        return;
      }
      if (onlySmall.length === 1) {
        this.featurePicks = [onlySmall[0], key];
        return;
      }
      this.featurePicks = [onlySmall[1], key];
    },
    selectToolkitAction(a) {
      if (!this.isPO) return;
      if (this.poToolkitDraft && this.poToolkitDraft.id === a.id) {
        this.poToolkitDraft = null;
        this.toolkitError = '';
        return;
      }
      this.toolkitError = '';
      this.poToolkitDraft = a;
    },
    clearToolkitDraft() {
      this.poToolkitDraft = null;
      this.toolkitError = '';
    },
    async confirmToolkitDraft() {
      if (!this.poToolkitDraft) return;
      await this.applyPoAction(this.poToolkitDraft);
      this.poToolkitDraft = null;
    },
    scrumPenaltyNarrative(sp) {
      const k = (sp && (sp.narrative_key || sp.reason)) || 'generic';
      const path = `agileTraining.pmSim.recap.scrumNarrative.${k}`;
      if (this.$te(path)) return this.$t(path);
      return this.$t('agileTraining.pmSim.recap.scrumNarrative.generic');
    },
    async confirmFeatureRelease(skip) {
      this.submitting = true;
      try {
        const keys = skip ? [] : this.featurePicks.map((k) => String(k));
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/feature/release`, {
          participant_token: this.participantToken, feature_keys: keys,
        });
        this.featurePicks = [];
        await this.loadState(true);
      } catch (e) {
        this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.submitting = false; }
    },
    async askAi(mode) {
      if (this.aiBusy) return;
      this.aiBusy = true;
      try {
        const res = await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken, mode, user_input: this.aiInput, locale: this.locale,
        });
        this.aiReply = res.data.reply || '';
        await this.loadState(true);
      } catch (e) {
        this.aiReply = (e.response && e.response.data && e.response.data.error) || 'Error';
      } finally { this.aiBusy = false; }
    },
    printReport() {
      window.print();
    },
    async applyPoAction(action) {
      if (!action || !action.id) return;
      if (this.submitting) return;
      this.submitting = true;
      this.toolkitError = '';
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/po-action`, {
          participant_token: this.participantToken,
          action_id: action.id,
          locale: this.locale,
        });
        await this.loadState(true);
      } catch (e) {
        const data = e.response && e.response.data;
        if (data && data.error === 'blocked' && (data.reasons || []).length) {
          this.toolkitError = this.$t('agileTraining.pmSim.toolkit.blocked', {
            reason: this.blockedReasonLabel(data.reasons[0]),
          });
        } else {
          this.toolkitError = (data && data.error) || e.message || 'Error';
        }
      } finally { this.submitting = false; }
    },
    blockedReasonLabel(reason) {
      if (!reason) return '';
      const key = String(reason).split(':')[0];
      const left = String(reason).includes(':') ? String(reason).split(':')[1] : null;
      const map = {
        cooldown: this.$t('agileTraining.pmSim.toolkit.blockedReason.cooldown', { n: left || 0 }),
        max_per_game: this.$t('agileTraining.pmSim.toolkit.blockedReason.max_per_game'),
        not_enough_capacity: this.$t('agileTraining.pmSim.toolkit.blockedReason.not_enough_capacity'),
        not_enough_budget: this.$t('agileTraining.pmSim.toolkit.blockedReason.not_enough_budget'),
        too_early: this.$t('agileTraining.pmSim.toolkit.blockedReason.too_early'),
        only_at_cycle_end: this.$t('agileTraining.pmSim.toolkit.blockedReason.only_at_cycle_end'),
        low_satisfaction: this.$t('agileTraining.pmSim.toolkit.blockedReason.low_satisfaction'),
        not_playing: this.$t('agileTraining.pmSim.toolkit.blockedReason.not_playing'),
        need_problem_interview: this.$t('agileTraining.pmSim.toolkit.blockedReason.need_problem_interview'),
        po_weekly_limit: this.$t('agileTraining.pmSim.toolkit.blockedReason.po_weekly_limit'),
      };
      return map[key] || reason;
    },
    syncQuotaDraft(value) {
      const src = value || this.state.quotas || {};
      const next = {};
      this.quotaFocusList.forEach((f) => {
        const v = Number(src[f]);
        next[f] = Number.isFinite(v) ? v : (this.quotaDefaults[f] || 0);
      });
      this.quotaDraft = next;
    },
    quotaDeviation(focus) {
      const actual = this.quotaActualPct[focus];
      if (actual === null || actual === undefined) return 0;
      const target = Number((this.state.quotas || {})[focus]) || 0;
      return Math.round(actual - target);
    },
    quotaDeviationText(focus) {
      const d = this.quotaDeviation(focus);
      return (d > 0 ? '+' : '') + d + ' pp';
    },
    quotaDeviationClass(focus) {
      const d = Math.abs(this.quotaDeviation(focus));
      const tol = Number(this.state.quota_tolerance_pct) || 18;
      const heavy = 22;
      if (d <= tol) return 'pmsim__quota-actual--ok';
      if (d >= heavy) return 'pmsim__quota-actual--bad';
      return 'pmsim__quota-actual--warn';
    },
    async saveQuotas() {
      if (!this.isPO) return;
      this.quotasError = '';
      if (!this.quotasDraftValid) {
        this.quotasError = this.quotaDraftSum === 100
          ? this.$t('agileTraining.pmSim.quotas.errors.range')
          : this.$t('agileTraining.pmSim.quotas.errors.sum');
        return;
      }
      this.quotasSaving = true;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/quotas`, {
          participant_token: this.participantToken,
          quotas: this.quotaDraft,
        });
        this.quotasSavedFlash = true;
        setTimeout(() => { this.quotasSavedFlash = false; }, 2000);
        await this.loadState(true);
      } catch (e) {
        const msg = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
        if (msg === 'quotas_must_sum_to_100') {
          this.quotasError = this.$t('agileTraining.pmSim.quotas.errors.sum');
        } else if (msg === 'invalid_quota_range' || msg === 'invalid_quota') {
          this.quotasError = this.$t('agileTraining.pmSim.quotas.errors.range');
        } else {
          this.quotasError = msg;
        }
      } finally {
        this.quotasSaving = false;
      }
    },
    localizeConsequenceStruct(arr) {
      if (!Array.isArray(arr) || !arr.length) return [];
      const out = [];
      arr.forEach((rec) => {
        if (!rec || typeof rec !== 'object') return;
        const k = rec.key || rec.type;
        const delta = Number(rec.delta);
        if (!Number.isFinite(delta) || delta === 0) return;
        out.push({ key: k, delta, label: this.effectLabel(k) });
      });
      return out;
    },
    closeRecap() {
      const r = this.recapToShow;
      if (r) this.recapDismissedWeek = r.week;
      this.recapForceShow = null;
    },
    showLatestRecap() {
      this.recapForceShow = null;
      this.recapDismissedWeek = -1;
    },
  },
};
</script>

<style scoped>
.pmsim { max-width: 1200px; margin: 0 auto; padding: 16px; color: #1f2937; }
.pmsim__top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.pmsim__brand { display: flex; align-items: center; gap: 12px; }
.pmsim__logo { font-size: 28px; }
.pmsim__title { font-size: 22px; font-weight: 700; color: #111827; }
.pmsim__sub { font-size: 13px; color: #6b7280; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.pmsim__dot { color: #9ca3af; }
.pmsim__status { font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.pmsim__status--alive { color: #065f46; background: #d1fae5; }
.pmsim__status--at_risk { color: #92400e; background: #fef3c7; }
.pmsim__status--dead { color: #7f1d1d; background: #fee2e2; }

.pmsim__lang button { border: 1px solid #cbd5e1; background: #fff; padding: 4px 10px; border-radius: 6px; margin-left: 4px; cursor: pointer; }
.pmsim__lang .act { background: #eef2ff; border-color: #6366f1; color: #4338ca; }

.pmsim__panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 22px; margin: 12px 0; }
.pmsim__lead { color: #374151; line-height: 1.55; }
.pmsim__form { display: flex; gap: 10px; margin-top: 14px; }
.pmsim__form input { flex: 1; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; }
.pmsim__btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #0f172a;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  line-height: 1.2;
  letter-spacing: normal;
  text-align: center;
  white-space: normal;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.pmsim__btn:hover:not(:disabled) { border-color: #94a3b8; background: #f8fafc; color: #0f172a; }
.pmsim__btn:disabled { opacity: 0.55; cursor: not-allowed; }
.pmsim__btn--primary {
  background: #4f46e5;
  color: #fff;
  border-color: #4338ca;
}
.pmsim__btn--primary:hover:not(:disabled) { background: #4338ca; border-color: #3730a3; color: #fff; }
.pmsim__btn--ghost { background: #f8fafc; color: #1f2937; }
.pmsim__btn--ghost:hover:not(:disabled) { background: #eef2ff; border-color: #c7d2fe; color: #1f2937; }
.pmsim__btn--danger { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
.pmsim__btn--danger:hover:not(:disabled) { background: #fee2e2; border-color: #fca5a5; color: #7f1d1d; }
.pmsim__btn--lg { padding: 10px 18px; font-size: 14px; }
.pmsim__error { color: #b91c1c; margin-top: 8px; }
.pmsim__hint { color: #6b7280; font-size: 13px; margin-top: 6px; }

.pmsim__roles { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-top: 8px; }
.pmsim__role { text-align: left; border: 1px solid #e2e8f0; background: #fff; border-radius: 10px; padding: 10px 12px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; }
.pmsim__role-icon { font-size: 22px; }
.pmsim__role-desc { color: #6b7280; font-size: 12px; }
.pmsim__role--active { border-color: #6366f1; background: #eef2ff; }
.pmsim__role--taken { opacity: 0.7; border-style: dashed; }

.pmsim__participants { margin-top: 14px; }
.pmsim__participants ul { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
.pmsim__participants li { background: #f1f5f9; padding: 6px 10px; border-radius: 999px; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; }
.pmsim__pcount { font-size: 13px; color: #6b7280; }
.pmsim__pill { background: #e0e7ff; color: #4338ca; padding: 1px 8px; border-radius: 999px; font-size: 11px; }
.pmsim__pill--ghost { background: #f1f5f9; color: #6b7280; }

.pmsim__cta { margin-top: 14px; display: flex; gap: 12px; align-items: center; }

.pmsim__dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 8px 0; }
.pmsim__metric { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px 12px; }
.pmsim__metric--money { background: linear-gradient(135deg,#ecfdf5,#d1fae5); border-color: #34d399; }
.pmsim__metric--debt { background: #fff7ed; border-color: #fdba74; }
.pmsim__metric--bad { background: #fef2f2; border-color: #fca5a5; }
.pmsim__metric--warn { background: #fffbeb; border-color: #fcd34d; }
.pmsim__m-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.04em; }
.pmsim__m-value { font-size: 22px; font-weight: 700; color: #0f172a; }
.pmsim__m-sub { font-size: 12px; color: #6b7280; }
.pmsim__m-bar { height: 6px; background: #e2e8f0; border-radius: 999px; margin-top: 6px; overflow: hidden; }
.pmsim__m-bar > span { display: block; height: 100%; background: #6366f1; }

.pmsim__charts h3 { margin: 14px 0 6px; }
.pmsim__chart-wrap { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }

.pmsim__risks { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
.pmsim__risk { background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 6px; font-size: 12px; }

.pmsim__event { background: #fff; border: 2px solid #6366f1; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__event-type { background: #ede9fe; color: #4338ca; padding: 2px 10px; border-radius: 999px; font-size: 12px; text-transform: uppercase; }
.pmsim__event h2 { margin: 6px 0 8px; }
.pmsim__event-desc { color: #374151; }

.pmsim__options { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 12px 0; }
.pmsim__option { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; }
.pmsim__option--mine { border-color: #22c55e; background: #f0fdf4; }
.pmsim__option--leading { border-color: #6366f1; }
.pmsim__option-head { display: flex; justify-content: space-between; align-items: center; }
.pmsim__votes { background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }

.pmsim__decision-bar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 10px; }
.pmsim__decision-bar select { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; }

.pmsim__features { background: #fff; border: 2px dashed #22c55e; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__capacity-line { font-size: 13px; color: #475569; }
.pmsim__feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
.pmsim__feature { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; cursor: pointer; transition: all .15s ease; }
.pmsim__feature:hover { border-color: #6366f1; }
.pmsim__feature--picked { border-color: #22c55e; background: #f0fdf4; }
.pmsim__feature header { display: flex; justify-content: space-between; }
.pmsim__feat-cap { background: #e0e7ff; color: #4338ca; padding: 1px 8px; border-radius: 999px; font-size: 12px; }
.pmsim__feat-effects { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; }
.pmsim__feat-effects li { background: #fff; padding: 2px 8px; border-radius: 999px; border: 1px solid #e2e8f0; }
.pmsim__fe-key { color: #64748b; margin-right: 4px; }
.pmsim__fe-value.pmsim__fe--up { color: #047857; }
.pmsim__fe-value.pmsim__fe--down { color: #b91c1c; }
.pmsim__feat-pick { color: #047857; font-weight: 700; margin-top: 6px; font-size: 12px; }
.pmsim__votes-row { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }

.pmsim__released { margin: 10px 0; }
.pmsim__released-list { display: flex; flex-wrap: wrap; gap: 6px; }
.pmsim__released-pill { background: #ecfdf5; border: 1px solid #34d399; color: #065f46; padding: 3px 8px; border-radius: 999px; font-size: 12px; }
.pmsim__released-pill--late { background: #fef3c7; border-color: #f59e0b; color: #92400e; }
.pmsim__late-tag { color: #92400e; font-style: normal; margin-left: 4px; font-weight: 600; }
.pmsim__late-tag--mini { font-size: 11px; padding: 0 4px; background: #fef3c7; border-radius: 6px; }

.pmsim__pending-line {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 13px;
  margin: 6px 0 0;
}

.pmsim__risk-pill {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}
.pmsim__risk-pill--ok   { background: #ecfdf5; color: #065f46; border-color: #34d399; }
.pmsim__risk-pill--low  { background: #ecfdf5; color: #065f46; border-color: #34d399; }
.pmsim__risk-pill--med  { background: #fef3c7; color: #92400e; border-color: #f59e0b; }
.pmsim__risk-pill--high { background: #fee2e2; color: #991b1b; border-color: #ef4444; }

.pmsim__consequences { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; }

.pmsim__ai { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; margin: 10px 0; }
.pmsim__ai textarea { width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; }
.pmsim__ai-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 6px; }
.pmsim__ai-counter { margin-left: auto; color: #6b7280; font-size: 12px; }
.pmsim__ai-reply { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; white-space: pre-wrap; font-family: inherit; margin-top: 8px; }

.pmsim__history ol { padding-left: 20px; }
.pmsim__history li { font-size: 13px; color: #334155; margin: 2px 0; }
.pmsim__history-effects { color: #6b7280; }

.pmsim__leader-hint { background: #eff6ff; border: 1px solid #93c5fd; color: #1e40af; padding: 8px 12px; border-radius: 8px; }

.pmsim__final { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__final-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
.pmsim__final-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; text-align: center; }
.pmsim__final-label { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
.pmsim__final-value { font-size: 28px; font-weight: 700; color: #0f172a; }
.pmsim__final-events { margin-top: 12px; }
.pmsim__final-events ol { padding-left: 20px; }

.pmsim__loading { padding: 16px; color: #6b7280; }

/* PO Toolkit */
.pmsim__toolkit {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; margin: 12px 0;
}
.pmsim__toolkit-head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.pmsim__toolkit-head h3 { margin: 0; font-size: 16px; }
.pmsim__toolkit-tabs { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
.pmsim__tk-tab {
  background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155;
  padding: 4px 12px; border-radius: 999px; cursor: pointer; font-size: 13px;
}
.pmsim__tk-tab--active { background: #4338ca; border-color: #4338ca; color: #fff; }
.pmsim__tk-count { opacity: 0.7; margin-left: 4px; font-size: 11px; }
.pmsim__toolkit-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px;
}
.pmsim__tk-card {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px;
  display: flex; flex-direction: column; gap: 6px; min-height: 180px;
}
.pmsim__tk-card--locked { opacity: 0.55; }
.pmsim__tk-card--discovery   { border-left: 3px solid #6366f1; }
.pmsim__tk-card--business    { border-left: 3px solid #0ea5e9; }
.pmsim__tk-card--engineering { border-left: 3px solid #14b8a6; }
.pmsim__tk-card--growth      { border-left: 3px solid #f59e0b; }
.pmsim__tk-card--pivot       { border-left: 3px solid #ef4444; }
.pmsim__tk-card--scrum       { border-left: 3px solid #10b981; }
.pmsim__tk-head { display: flex; align-items: center; gap: 6px; }
.pmsim__tk-icon { font-size: 18px; }
.pmsim__tk-desc { font-size: 12px; color: #475569; margin: 0; }
.pmsim__tk-effects {
  list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 4px 8px; font-size: 11px;
}
.pmsim__tk-effects li { display: flex; gap: 3px; }
.pmsim__tk-foot { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: auto; }
.pmsim__tk-card--selectable { cursor: pointer; }
.pmsim__tk-card--draft { box-shadow: 0 0 0 2px #6366f1; }
.pmsim__toolkit-bar {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 12px;
  padding: 10px 12px; background: #f1f5f9; border-radius: 10px; border: 1px solid #e2e8f0;
}
.pmsim__tk-draft-label { font-size: 13px; color: #312e81; }
.pmsim__toolkit-bar-btns { display: flex; gap: 8px; }
.pmsim__recap-scrum-list { margin: 6px 0 0; padding-left: 18px; }
.pmsim__recap-scrum-list .pmsim__hint { margin: 0 0 6px; }
.pmsim__tk-error { color: #b91c1c; font-size: 12px; margin-top: 8px; }

/* Weekly Recap modal */
.pmsim__recap-overlay {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55);
  display: flex; justify-content: center; align-items: flex-start;
  padding: 40px 16px; z-index: 80; overflow: auto;
}
.pmsim__recap {
  background: #fff; border-radius: 16px; max-width: 560px; width: 100%;
  padding: 20px 22px; box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  display: flex; flex-direction: column; gap: 8px;
}
.pmsim__recap-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.pmsim__recap-head h3 { margin: 0; font-size: 18px; color: #0f172a; }
.pmsim__recap-x {
  background: transparent; border: 0; font-size: 24px; line-height: 1; color: #64748b; cursor: pointer;
}
.pmsim__recap-lead { font-size: 13px; color: #475569; margin: 0 0 8px 0; }
.pmsim__recap-section { border-top: 1px dashed #e2e8f0; padding-top: 8px; margin-top: 4px; }
.pmsim__recap-section h4 { margin: 0 0 4px 0; font-size: 13px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.03em; }
.pmsim__recap-section ul { margin: 4px 0 0 16px; padding: 0; font-size: 13px; color: #1e293b; }
.pmsim__recap-deltas { list-style: none; padding: 0; margin: 0; display: grid; gap: 4px; }
.pmsim__recap-delta {
  display: flex; justify-content: space-between; padding: 4px 8px; border-radius: 6px;
  background: #f8fafc; font-size: 13px;
}
.pmsim__recap-delta--up { background: #ecfdf5; color: #065f46; }
.pmsim__recap-delta--down { background: #fef2f2; color: #7f1d1d; }
.pmsim__recap-key { font-weight: 600; }
.pmsim__recap-vals em { font-style: normal; opacity: 0.7; margin-left: 4px; }
.pmsim__recap-focus { background: #eef2ff; border-radius: 8px; padding: 8px 10px; }
.pmsim__recap-focus h4 { color: #312e81; }
.pmsim__recap-focus p { margin: 0; font-size: 13px; color: #312e81; }
.pmsim__recap-foot { display: flex; justify-content: flex-end; margin-top: 8px; }

/* PO weekly action budget */
.pmsim__toolkit-head { align-items: flex-start; }
.pmsim__po-budget {
  display: inline-flex; flex-direction: column; align-items: flex-end; gap: 2px;
  background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 10px;
  padding: 6px 10px; max-width: 320px;
}
.pmsim__po-budget-label { font-size: 11px; color: #4338ca; text-transform: uppercase; letter-spacing: 0.04em; }
.pmsim__po-budget-value { font-size: 16px; color: #1e1b4b; }
.pmsim__po-budget .pmsim__hint { margin: 0; font-size: 11px; color: #4338ca; text-align: right; }

/* Focus tag (business / tech_debt / architecture) */
.pmsim__focus-tag {
  display: inline-flex; align-items: center; padding: 1px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 600; line-height: 1.4; border: 1px solid transparent;
  margin-left: 6px; white-space: nowrap;
}
.pmsim__focus-tag--business     { background: #ecfeff; color: #155e75; border-color: #67e8f9; }
.pmsim__focus-tag--tech_debt    { background: #fff7ed; color: #9a3412; border-color: #fdba74; }
.pmsim__focus-tag--architecture { background: #f5f3ff; color: #4c1d95; border-color: #c4b5fd; }

/* Feature card extras */
.pmsim__feat-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin: 4px 0 0; }
.pmsim__pick-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 999px; border: 1px solid transparent;
  text-transform: uppercase; letter-spacing: 0.03em; font-weight: 600;
}
.pmsim__pick-badge--solo  { background: #ecfdf5; color: #065f46; border-color: #6ee7b7; }
.pmsim__pick-badge--big   { background: #fef3c7; color: #92400e; border-color: #fbbf24; }
.pmsim__pick-badge--small { background: #f1f5f9; color: #1e293b; border-color: #cbd5e1; }
.pmsim__feature--big { border-style: dashed; }
.pmsim__feature--stabilize header strong { color: #047857; }
.pmsim__pick-help {
  background: #eef2ff; border: 1px solid #c7d2fe; color: #312e81;
  padding: 6px 10px; border-radius: 8px; font-size: 12px; margin: 6px 0;
}

/* Quotas widget */
.pmsim__quotas { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__quotas-head { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.pmsim__quotas-head h3 { margin: 0; font-size: 16px; }
.pmsim__quotas-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
.pmsim__quota-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; }
.pmsim__quota-card--business     { border-left: 3px solid #0ea5e9; }
.pmsim__quota-card--tech_debt    { border-left: 3px solid #f97316; }
.pmsim__quota-card--architecture { border-left: 3px solid #8b5cf6; }
.pmsim__quota-label { font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.03em; font-weight: 600; }
.pmsim__quota-input-row { display: flex; align-items: center; gap: 4px; }
.pmsim__quota-input-row input {
  width: 70px; padding: 6px 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: 700;
  background: #fff;
}
.pmsim__quota-input-row input:disabled { background: #f1f5f9; color: #475569; }
.pmsim__quota-unit { color: #64748b; font-size: 13px; }
.pmsim__quota-actual { font-size: 12px; color: #475569; display: flex; flex-direction: column; gap: 2px; margin-top: 4px; }
.pmsim__quota-actual strong { font-size: 13px; }
.pmsim__quota-dev { font-style: normal; opacity: 0.85; margin-left: 4px; font-size: 11px; }
.pmsim__quota-actual--ok strong   { color: #065f46; }
.pmsim__quota-actual--warn strong { color: #92400e; }
.pmsim__quota-actual--bad strong  { color: #991b1b; }
.pmsim__quotas-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.pmsim__hint--ok { color: #065f46; }

/* Consequences pills */
.pmsim__cons-list { display: inline-flex; flex-wrap: wrap; gap: 4px; margin-left: 6px; }
.pmsim__cons-pill {
  display: inline-flex; align-items: center; padding: 1px 8px; border-radius: 999px;
  font-size: 12px; background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; font-weight: 600;
}
.pmsim__cons-pill--up   { background: #ecfdf5; color: #065f46; border-color: #6ee7b7; }
.pmsim__cons-pill--down { background: #fef2f2; color: #7f1d1d; border-color: #fca5a5; }

/* Recap quotas */
.pmsim__recap-quota-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 4px; font-size: 13px; }
.pmsim__recap-quota-list em { font-style: normal; margin-left: 4px; }

@media print {
  .pmsim__top, .pmsim__lang, .pmsim__ai, .pmsim__cta, .pmsim__decision-bar, .pmsim__btn { display: none !important; }
  .pmsim__panel, .pmsim__final { box-shadow: none; border-color: #cbd5e1; }
  body { background: #fff; }
}
</style>

<template>
  <div class="bv-page">
    <header class="bv-head">
      <router-link to="/new" class="bv-back">← {{ $t('businessValue.backHome') }}</router-link>
      <h1>{{ $t('businessValue.title') }}</h1>
      <p class="bv-lead">{{ $t('businessValue.lead') }}</p>
      <p class="bv-formula muted">{{ $t('businessValue.formulaHint') }}</p>
    </header>

    <section class="bv-card">
      <h2>{{ $t('businessValue.factorsTitle') }}</h2>
      <p class="muted small">{{ $t('businessValue.factorsHint') }}</p>
      <p class="bv-scale-legend muted small">{{ $t('businessValue.scaleLegend') }}</p>
      <div class="bv-factor-list">
        <div
          v-for="f in allFactors"
          :key="f.id"
          class="bv-factor-block"
          :class="{ 'bv-factor-block--on': selectedFactorIds.includes(f.id) }"
        >
          <div class="bv-factor-block-head">
            <label class="bv-factor-check">
              <input v-model="selectedFactorIds" type="checkbox" :value="f.id" />
              <span class="bv-factor-label">{{ factorLabel(f) }}</span>
              <span class="bv-factor-pol">{{ f.polarity < 0 ? '−' : '+' }}</span>
            </label>
            <button
              v-if="f.custom"
              type="button"
              class="bv-remove-criterion"
              :title="$t('businessValue.removeCriterion')"
              @click.prevent="removeCustomFactor(f.id)"
            >
              ×
            </button>
          </div>
          <div class="bv-factor-hints">
            <p><span class="bv-hint-tag">{{ $t('businessValue.hint1Short') }}</span> {{ hint1(f) }}</p>
            <p><span class="bv-hint-tag">{{ $t('businessValue.hint5Short') }}</span> {{ hint5(f) }}</p>
          </div>
        </div>
      </div>

      <div class="bv-custom-block">
        <h3 class="bv-custom-title">{{ $t('businessValue.customBlockTitle') }}</h3>
        <div class="bv-custom-grid">
          <div>
            <label class="bv-label">{{ $t('businessValue.customName') }}</label>
            <input v-model="customDraft.name" type="text" class="bv-input" maxlength="120" />
          </div>
          <div>
            <label class="bv-label">{{ $t('businessValue.customPolarity') }}</label>
            <select v-model.number="customDraft.polarity" class="bv-input">
              <option :value="1">{{ $t('businessValue.customAdds') }}</option>
              <option :value="-1">{{ $t('businessValue.customSubtracts') }}</option>
            </select>
          </div>
          <div class="bv-custom-span2">
            <label class="bv-label">{{ $t('businessValue.customHintLow') }}</label>
            <input v-model="customDraft.hint1" type="text" class="bv-input" maxlength="240" />
          </div>
          <div class="bv-custom-span2">
            <label class="bv-label">{{ $t('businessValue.customHintHigh') }}</label>
            <input v-model="customDraft.hint5" type="text" class="bv-input" maxlength="240" />
          </div>
        </div>
        <button type="button" class="bv-btn bv-btn-primary bv-add-custom" @click="addCustomFactor">
          {{ $t('businessValue.addCustom') }}
        </button>
      </div>
    </section>

    <section class="bv-card">
      <h2>{{ $t('businessValue.loadTitle') }}</h2>
      <div class="bv-load-grid">
        <div>
          <label class="bv-label">{{ $t('businessValue.pasteLabel') }}</label>
          <textarea v-model="pasteText" class="bv-textarea" rows="8" :placeholder="$t('businessValue.pastePlaceholder')" />
          <div class="bv-row">
            <button type="button" class="bv-btn" @click="addLinesAsItems">{{ $t('businessValue.addLines') }}</button>
            <button type="button" class="bv-btn bv-btn-primary" :disabled="parseTextLoading" @click="parseFromText">
              {{ parseTextLoading ? '…' : $t('businessValue.parseAi') }}
            </button>
          </div>
        </div>
        <div>
          <label class="bv-label">{{ $t('businessValue.imageLabel') }}</label>
          <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp" class="bv-file" @change="onFile" />
          <button type="button" class="bv-btn bv-btn-primary" :disabled="parseImageLoading || !imageFile" @click="parseFromImage">
            {{ parseImageLoading ? '…' : $t('businessValue.parseImage') }}
          </button>
          <p v-if="parseError" class="bv-err">{{ parseError }}</p>
        </div>
      </div>
    </section>

    <section v-if="items.length" class="bv-card">
      <div class="bv-toolbar">
        <h2>{{ $t('businessValue.tableTitle', { n: items.length }) }}</h2>
        <div class="bv-toolbar-actions">
          <button type="button" class="bv-btn" @click="copyJiraWiki">{{ $t('businessValue.copyJira') }}</button>
          <button type="button" class="bv-btn" @click="downloadCsv">{{ $t('businessValue.downloadCsv') }}</button>
          <button type="button" class="bv-btn" @click="downloadTxt">{{ $t('businessValue.downloadTxt') }}</button>
        </div>
      </div>
      <div class="bv-table-wrap">
        <table class="bv-table">
          <thead>
            <tr>
              <th>#</th>
              <th>{{ $t('businessValue.colItem') }}</th>
              <th
                v-for="fid in selectedFactorIds"
                :key="fid"
                class="bv-th-factor"
                :title="columnTooltip(fid)"
              >
                <span class="bv-th-name">{{ shortFactorLabel(fid) }}</span>
              </th>
              <th>{{ $t('businessValue.colScore') }}</th>
              <th>{{ $t('businessValue.colDecision') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in items" :key="row.id">
              <td>{{ idx + 1 }}</td>
              <td>
                <div class="bv-item-title">{{ row.title }}</div>
                <div v-if="row.description" class="bv-item-desc muted small">{{ row.description }}</div>
              </td>
              <td v-for="fid in selectedFactorIds" :key="row.id + fid" class="bv-score-cell">
                <select v-model.number="row.scores[fid]" class="bv-select" :title="columnTooltip(fid)">
                  <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
                </select>
                <div class="bv-cell-hints muted tiny">{{ cellHintLine(fid) }}</div>
              </td>
              <td><strong>{{ scoreRow(row).toFixed(0) }}</strong></td>
              <td>
                <span class="bv-badge" :class="'bv-badge--' + bandKey(row)">{{ bandLabel(row) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else class="bv-card bv-card--muted">
      <p>{{ $t('businessValue.emptyState') }}</p>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

function authHeaders() {
  const t = localStorage.getItem('token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/** Выбранные критерии и свои факторы — последнее состояние в этом браузере. */
const BV_SELECTION_STORAGE_KEY = 'growboard_business_value_selection_v1';
const MAX_CUSTOM_FACTORS_STORED = 15;

export default {
  name: 'BusinessValueAssessment',
  data() {
    return {
      factors: [],
      customFactors: [],
      customDraft: { name: '', hint1: '', hint5: '', polarity: 1 },
      selectedFactorIds: ['profit', 'urgency', 'regulatory', 'delivery_risk'],
      items: [],
      pasteText: '',
      imageFile: null,
      parseTextLoading: false,
      parseImageLoading: false,
      parseError: null,
      persistBvReady: false
    };
  },
  computed: {
    allFactors() {
      return [...(this.factors || []), ...(this.customFactors || [])];
    },
    factorById() {
      const m = {};
      for (const f of this.allFactors) m[f.id] = f;
      return m;
    }
  },
  async mounted() {
    try {
      const res = await axios.get('/api/business-value/factors');
      this.factors = res.data.factors || [];
    } catch {
      this.factors = [];
    }
    this._loadBvPersisted();
    this.persistBvReady = true;
    this._persistBvSelection();
  },
  methods: {
    _normalizeStoredCustom(cf) {
      if (!cf || typeof cf !== 'object') return null;
      const id = String(cf.id || '');
      if (!id.startsWith('custom:')) return null;
      const pol = Number(cf.polarity) < 0 ? -1 : 1;
      const lr = String(cf.label_ru || cf.label || '').trim().slice(0, 120);
      if (!lr) return null;
      const le = String(cf.label_en || lr).trim().slice(0, 120);
      const defLo = this.$t('businessValue.defaultHintLow');
      const defHi = this.$t('businessValue.defaultHintHigh');
      const h1r = String(cf.hint1_ru || cf.hint1 || '').trim().slice(0, 240);
      const h5r = String(cf.hint5_ru || cf.hint5 || '').trim().slice(0, 240);
      return {
        id,
        polarity: pol,
        label_ru: lr,
        label_en: le,
        hint1_ru: h1r || defLo,
        hint5_ru: h5r || defHi,
        hint1_en: String(cf.hint1_en || h1r || '').trim().slice(0, 240) || defLo,
        hint5_en: String(cf.hint5_en || h5r || '').trim().slice(0, 240) || defHi,
        custom: true
      };
    },
    _loadBvPersisted() {
      try {
        const raw = localStorage.getItem(BV_SELECTION_STORAGE_KEY);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (Array.isArray(data.customFactors)) {
          const list = data.customFactors.map((x) => this._normalizeStoredCustom(x)).filter(Boolean);
          this.customFactors = list.slice(0, MAX_CUSTOM_FACTORS_STORED);
        }
        const builtInIds = new Set((this.factors || []).map((f) => f.id));
        const customIds = new Set(this.customFactors.map((f) => f.id));
        if (Array.isArray(data.selectedFactorIds) && data.selectedFactorIds.length) {
          const picked = data.selectedFactorIds.filter(
            (id) => typeof id === 'string' && (builtInIds.has(id) || customIds.has(id))
          );
          if (picked.length) {
            this.selectedFactorIds = picked;
          }
        }
      } catch (_e) {
        /* ignore */
      }
    },
    _persistBvSelection() {
      if (!this.persistBvReady) return;
      try {
        localStorage.setItem(
          BV_SELECTION_STORAGE_KEY,
          JSON.stringify({
            selectedFactorIds: this.selectedFactorIds,
            customFactors: this.customFactors
          })
        );
      } catch (_e) {
        /* ignore */
      }
    },
    _newCustomId() {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) return `custom:${crypto.randomUUID()}`;
      return `custom:${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    },
    hint1(f) {
      if (!f) return '';
      const en = this.$i18n?.locale === 'en';
      return en ? (f.hint1_en || f.hint1_ru || '') : (f.hint1_ru || f.hint1_en || '');
    },
    hint5(f) {
      if (!f) return '';
      const en = this.$i18n?.locale === 'en';
      return en ? (f.hint5_en || f.hint5_ru || '') : (f.hint5_ru || f.hint5_en || '');
    },
    columnTooltip(fid) {
      const f = this.factorById[fid];
      if (!f) return '';
      const a = this.hint1(f);
      const b = this.hint5(f);
      return `1 — ${a}\n5 — ${b}`;
    },
    cellHintLine(fid) {
      const f = this.factorById[fid];
      if (!f) return '';
      const a = this.shortHint(this.hint1(f), 42);
      const b = this.shortHint(this.hint5(f), 42);
      return `${this.$t('businessValue.hint1Short')}: ${a} · ${this.$t('businessValue.hint5Short')}: ${b}`;
    },
    shortHint(s, maxLen) {
      if (!s) return '—';
      return s.length <= maxLen ? s : `${s.slice(0, maxLen - 1)}…`;
    },
    addCustomFactor() {
      const name = (this.customDraft.name || '').trim();
      if (!name) return;
      const h1 = (this.customDraft.hint1 || '').trim() || this.$t('businessValue.defaultHintLow');
      const h5 = (this.customDraft.hint5 || '').trim() || this.$t('businessValue.defaultHintHigh');
      const pol = Number(this.customDraft.polarity) < 0 ? -1 : 1;
      const id = this._newCustomId();
      this.customFactors.push({
        id,
        polarity: pol,
        label_ru: name,
        label_en: name,
        hint1_ru: h1,
        hint5_ru: h5,
        hint1_en: h1,
        hint5_en: h5,
        custom: true
      });
      if (!this.selectedFactorIds.includes(id)) {
        this.selectedFactorIds = [...this.selectedFactorIds, id];
      }
      this.customDraft = { name: '', hint1: '', hint5: '', polarity: 1 };
      for (const row of this.items) this.ensureScores(row);
      this._persistBvSelection();
    },
    removeCustomFactor(id) {
      if (!id || !String(id).startsWith('custom:')) return;
      this.customFactors = this.customFactors.filter((f) => f.id !== id);
      this.selectedFactorIds = this.selectedFactorIds.filter((x) => x !== id);
      for (const row of this.items) {
        if (row.scores && Object.prototype.hasOwnProperty.call(row.scores, id)) {
          delete row.scores[id];
        }
      }
      this._persistBvSelection();
    },
    factorLabel(f) {
      const en = this.$i18n?.locale === 'en';
      return en ? (f.label_en || f.label_ru) : (f.label_ru || f.label_en);
    },
    shortFactorLabel(fid) {
      const f = this.factorById[fid];
      if (!f) return fid;
      const s = this.factorLabel(f);
      return s.length > 18 ? s.slice(0, 16) + '…' : s;
    },
    ensureScores(row) {
      if (!row.scores) row.scores = {};
      for (const fid of this.selectedFactorIds) {
        if (row.scores[fid] == null || row.scores[fid] === '') row.scores[fid] = 3;
      }
    },
    scoreRow(row) {
      if (!this.selectedFactorIds.length) return 0;
      let total = 0;
      for (const fid of this.selectedFactorIds) {
        const f = this.factorById[fid];
        if (!f) continue;
        const v = Number(row.scores && row.scores[fid]);
        const n = Number.isFinite(v) && v >= 1 && v <= 5 ? v : 3;
        total += n * (f.polarity || 1);
      }
      return total;
    },
    bandKey(row) {
      const s = this.scoreRow(row);
      if (s >= 12) return 'immediate';
      if (s >= 7) return 'quarter';
      return 'defer';
    },
    bandLabel(row) {
      const k = this.bandKey(row);
      return this.$t(`businessValue.band.${k}`);
    },
    addLinesAsItems() {
      const lines = this.pasteText.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
      for (const line of lines) {
        const id = `local-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        const row = { id, title: line, description: '', item_type: 'story', scores: {} };
        this.ensureScores(row);
        this.items.push(row);
      }
      this.parseError = null;
    },
    async parseFromText() {
      const text = this.pasteText.trim();
      if (!text) return;
      this.parseTextLoading = true;
      this.parseError = null;
      try {
        const res = await axios.post(
          '/api/business-value/parse-items',
          { text },
          { headers: { ...authHeaders() }, params: { lang: this.$i18n.locale === 'en' ? 'en' : 'ru' } }
        );
        this.mergeItems(res.data.items || []);
      } catch (e) {
        this.parseError = e.response?.data?.error || e.message || 'Error';
      } finally {
        this.parseTextLoading = false;
      }
    },
    onFile(e) {
      const f = e.target.files && e.target.files[0];
      this.imageFile = f || null;
    },
    async parseFromImage() {
      if (!this.imageFile) return;
      this.parseImageLoading = true;
      this.parseError = null;
      const fd = new FormData();
      fd.append('image', this.imageFile);
      try {
        const res = await axios.post('/api/business-value/parse-items', fd, {
          headers: { ...authHeaders() },
          params: { lang: this.$i18n.locale === 'en' ? 'en' : 'ru' }
        });
        this.mergeItems(res.data.items || []);
      } catch (e) {
        this.parseError = e.response?.data?.error || e.message || 'Error';
      } finally {
        this.parseImageLoading = false;
      }
    },
    mergeItems(raw) {
      for (const it of raw) {
        const row = {
          id: it.id || `id-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          title: it.title || '—',
          description: it.description || '',
          item_type: it.item_type || 'story',
          scores: {}
        };
        this.ensureScores(row);
        this.items.push(row);
      }
    },
    buildRowsForExport() {
      return this.items.map((row) => {
        const cells = {};
        for (const fid of this.selectedFactorIds) {
          cells[fid] = row.scores && row.scores[fid] != null ? row.scores[fid] : '';
        }
        return {
          title: row.title,
          description: row.description,
          score: this.scoreRow(row),
          band: this.bandLabel(row),
          cells
        };
      });
    },
    jiraWikiTable() {
      const headers = [this.$t('businessValue.colItem'), ...this.selectedFactorIds.map((fid) => this.shortFactorLabel(fid)), this.$t('businessValue.colScore'), this.$t('businessValue.colDecision')];
      const head = `||${headers.join('||')}||`;
      const lines = this.buildRowsForExport().map((r) => {
        const parts = [r.title.replace(/\|/g, '/')];
        for (const fid of this.selectedFactorIds) {
          parts.push(String(r.cells[fid] ?? ''));
        }
        parts.push(String(Math.round(r.score)));
        parts.push(r.band.replace(/\|/g, '/'));
        return `|${parts.join('|')}|`;
      });
      return [head, ...lines].join('\n');
    },
    async copyJiraWiki() {
      const text = this.jiraWikiTable();
      try {
        await navigator.clipboard.writeText(text);
        alert(this.$t('businessValue.copied'));
      } catch {
        alert(this.$t('businessValue.copyFallback'));
      }
    },
    downloadCsv() {
      const sep = ';';
      const h = ['title', ...this.selectedFactorIds, 'score', 'band'];
      const rows = this.buildRowsForExport().map((r) => {
        const esc = (s) => `"${String(s).replace(/"/g, '""')}"`;
        const parts = [esc(r.title)];
        for (const fid of this.selectedFactorIds) parts.push(String(r.cells[fid] ?? ''));
        parts.push(String(Math.round(r.score)));
        parts.push(esc(r.band));
        return parts.join(sep);
      });
      const blob = new Blob([`\uFEFF${h.join(sep)}\n${rows.join('\n')}`], { type: 'text/csv;charset=utf-8' });
      this._downloadBlob(blob, 'business-value.csv');
    },
    downloadTxt() {
      const lines = this.buildRowsForExport().map(
        (r) => `${r.title}\n  ${this.$t('businessValue.colScore')}: ${Math.round(r.score)} — ${r.band}\n`
      );
      const intro = `${this.$t('businessValue.title')}\n${this.$t('businessValue.formulaHint')}\n\n`;
      const blob = new Blob([intro + lines.join('\n')], { type: 'text/plain;charset=utf-8' });
      this._downloadBlob(blob, 'business-value.txt');
    },
    _downloadBlob(blob, name) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      URL.revokeObjectURL(a.href);
    }
  },
  watch: {
    selectedFactorIds: {
      deep: true,
      handler(ids) {
        if (!ids || !ids.length) {
          const first = (this.allFactors && this.allFactors[0] && this.allFactors[0].id) || 'profit';
          this.selectedFactorIds = [first];
          return;
        }
        for (const row of this.items) this.ensureScores(row);
        this._persistBvSelection();
      }
    },
    customFactors: {
      deep: true,
      handler() {
        this._persistBvSelection();
      }
    }
  }
};
</script>

<style scoped>
.bv-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  background: linear-gradient(180deg, #f4f7ff 0%, #fff 40%);
  min-height: 100vh;
}

.bv-head {
  margin-bottom: 24px;
}

.bv-back {
  display: inline-block;
  margin-bottom: 12px;
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

.bv-head h1 {
  margin: 0 0 8px;
  font-size: 1.65rem;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.bv-lead {
  margin: 0 0 8px;
  color: #475569;
  max-width: 720px;
  line-height: 1.5;
}

.bv-formula {
  font-size: 0.9rem;
}

.muted {
  color: #64748b;
}

.small {
  font-size: 0.82rem;
}

.bv-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.bv-card--muted {
  text-align: center;
  color: #64748b;
}

.bv-card h2 {
  margin: 0 0 10px;
  font-size: 1.1rem;
  color: #0f172a;
}

.bv-scale-legend {
  margin: 0 0 14px;
  max-width: 820px;
  line-height: 1.45;
}

.bv-factor-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bv-factor-block {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px 14px;
  background: #f8fafc;
}

.bv-factor-block--on {
  border-color: #2563eb;
  background: #eff6ff;
}

.bv-factor-block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.bv-factor-check {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.bv-remove-criterion {
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 1.35rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
}

.bv-remove-criterion:hover {
  color: #b91c1c;
}

.bv-factor-hints {
  margin: 10px 0 0 26px;
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.4;
}

.bv-factor-hints p {
  margin: 4px 0;
}

.bv-hint-tag {
  display: inline-block;
  min-width: 1.25rem;
  font-weight: 800;
  color: #2563eb;
}

.bv-custom-block {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #e2e8f0;
}

.bv-custom-title {
  margin: 0 0 12px;
  font-size: 1rem;
  color: #0f172a;
}

.bv-custom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}

.bv-custom-span2 {
  grid-column: 1 / -1;
}

@media (max-width: 640px) {
  .bv-custom-grid {
    grid-template-columns: 1fr;
  }
  .bv-custom-span2 {
    grid-column: auto;
  }
}

.bv-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 0.9rem;
}

.bv-add-custom {
  margin-top: 12px;
}

.bv-factor-label {
  font-size: 0.9rem;
  color: #1e293b;
  font-weight: 600;
}

.bv-factor-pol {
  font-weight: 800;
  color: #64748b;
  font-size: 0.85rem;
}

.tiny {
  font-size: 0.72rem;
  line-height: 1.25;
}

.bv-th-factor {
  max-width: 140px;
  vertical-align: bottom;
}

.bv-th-name {
  display: inline-block;
  max-width: 120px;
  white-space: normal;
  line-height: 1.2;
}

.bv-score-cell {
  max-width: 130px;
}

.bv-cell-hints {
  margin-top: 4px;
}

.bv-load-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 800px) {
  .bv-load-grid {
    grid-template-columns: 1fr;
  }
}

.bv-label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 0.88rem;
}

.bv-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  padding: 10px;
  font-family: inherit;
  resize: vertical;
}

.bv-file {
  display: block;
  margin-bottom: 10px;
}

.bv-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.bv-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 10px;
  padding: 8px 14px;
  font-weight: 600;
  cursor: pointer;
  color: #1e293b;
}

.bv-btn-primary {
  background: linear-gradient(145deg, #1d4ed8, #2563eb);
  color: #fff;
  border-color: transparent;
}

.bv-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.bv-err {
  color: #b91c1c;
  font-size: 0.88rem;
  margin-top: 8px;
}

.bv-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.bv-toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.bv-table-wrap {
  overflow-x: auto;
}

.bv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.bv-table th,
.bv-table td {
  border-bottom: 1px solid #e2e8f0;
  padding: 8px 6px;
  text-align: left;
  vertical-align: top;
}

.bv-table th {
  background: #f1f5f9;
  font-weight: 700;
  white-space: nowrap;
}

.bv-select {
  min-width: 52px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  padding: 4px;
}

.bv-item-title {
  font-weight: 600;
  color: #0f172a;
}

.bv-item-desc {
  margin-top: 4px;
}

.bv-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
}

.bv-badge--immediate {
  background: #fee2e2;
  color: #991b1b;
}

.bv-badge--quarter {
  background: #fef9c3;
  color: #854d0e;
}

.bv-badge--defer {
  background: #f3e8ff;
  color: #6b21a8;
}
</style>

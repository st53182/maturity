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
      <div class="bv-factor-grid">
        <label
          v-for="f in factors"
          :key="f.id"
          class="bv-factor-chip"
          :class="{ 'bv-factor-chip--on': selectedFactorIds.includes(f.id) }"
        >
          <input v-model="selectedFactorIds" type="checkbox" :value="f.id" />
          <span class="bv-factor-label">{{ factorLabel(f) }}</span>
          <span class="bv-factor-pol">{{ f.polarity < 0 ? '−' : '+' }}</span>
        </label>
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
              <th v-for="fid in selectedFactorIds" :key="fid">{{ shortFactorLabel(fid) }}</th>
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
              <td v-for="fid in selectedFactorIds" :key="row.id + fid">
                <select v-model.number="row.scores[fid]" class="bv-select">
                  <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
                </select>
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

export default {
  name: 'BusinessValueAssessment',
  data() {
    return {
      factors: [],
      selectedFactorIds: ['profit', 'urgency', 'regulatory', 'delivery_risk'],
      items: [],
      pasteText: '',
      imageFile: null,
      parseTextLoading: false,
      parseImageLoading: false,
      parseError: null
    };
  },
  computed: {
    factorById() {
      const m = {};
      for (const f of this.factors) m[f.id] = f;
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
  },
  methods: {
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
          this.selectedFactorIds = ['profit'];
        }
        for (const row of this.items) this.ensureScores(row);
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

.bv-factor-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.bv-factor-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  cursor: pointer;
  background: #f8fafc;
}

.bv-factor-chip--on {
  border-color: #2563eb;
  background: #eff6ff;
}

.bv-factor-label {
  font-size: 0.88rem;
  color: #1e293b;
}

.bv-factor-pol {
  font-weight: 800;
  color: #64748b;
  font-size: 0.85rem;
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

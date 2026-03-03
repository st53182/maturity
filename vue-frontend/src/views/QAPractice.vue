<template>
  <div class="qa-practice">
    <header class="qa-header">
      <h1>🔍 {{ $t('qa.title') }}</h1>
      <p class="qa-subtitle">{{ $t('qa.subtitle') }}</p>
      <p class="qa-hint">{{ $t('qa.linkHint') }} <code>{{ qaLink }}</code></p>
    </header>

    <!-- Список практикумов -->
    <div v-if="currentPuzzle === null" class="puzzles-grid">
      <div class="puzzle-card" @click="currentPuzzle = 'triangle'">
        <span class="puzzle-icon">🔺</span>
        <h2>{{ $t('qa.puzzleTriangleTitle') }}</h2>
        <p>{{ $t('qa.puzzleTriangleDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="currentPuzzle = 'shop'">
        <span class="puzzle-icon">🛒</span>
        <h2>{{ $t('qa.puzzleShopTitle') }}</h2>
        <p>{{ $t('qa.puzzleShopDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
    </div>

    <!-- Кнопка назад -->
    <button v-else class="back-btn" @click="currentPuzzle = null">← {{ $t('qa.backToList') }}</button>

    <!-- Практикум: Треугольник -->
    <section v-if="currentPuzzle === 'triangle'" class="puzzle-section triangle-puzzle">
      <h2>🔺 {{ $t('qa.puzzleTriangleTitle') }}</h2>
      <p class="puzzle-intro">{{ $t('qa.triangleIntro') }}</p>

      <div class="progress-row">
        <span>{{ $t('qa.bugsFound') }} {{ triangleBugsFound.length }} / 4</span>
        <span>{{ $t('qa.casesTried') }} {{ triangleCasesTried.size }} / 6</span>
      </div>

      <div class="bugs-list">
        <div v-for="i in 4" :key="i" class="bug-slot" :class="{ found: triangleBugsFound.includes(i) }">
          {{ triangleBugsFound.includes(i) ? $t('qa.bugRevealed') + ' ' + i : $t('qa.bugHidden') }}
        </div>
      </div>

      <div class="triangle-form">
        <div class="input-row">
          <label>{{ $t('qa.sideA') }}</label>
          <input v-model.number="triangle.a" type="number" min="0" step="any" />
        </div>
        <div class="input-row">
          <label>{{ $t('qa.sideB') }}</label>
          <input v-model.number="triangle.b" type="number" min="0" step="any" />
        </div>
        <div class="input-row">
          <label>{{ $t('qa.sideC') }}</label>
          <input v-model.number="triangle.c" type="number" min="0" step="any" />
        </div>
        <button class="submit-btn" @click="checkTriangle">{{ $t('qa.determineType') }}</button>
      </div>

      <div v-if="triangleResult !== null" class="result-box" :class="{ bug: triangleResultIsBug }">
        <strong>{{ $t('qa.result') }}:</strong> {{ triangleResult }}
        <p v-if="triangleResultIsBug" class="bug-found-msg">🎉 {{ $t('qa.bugFound') }}</p>
      </div>

      <div v-if="triangleBugsFound.length === 4" class="surprise-msg">🎊 {{ $t('qa.allBugsFound') }}</div>
    </section>

    <!-- Практикум: Мини-магазин -->
    <section v-if="currentPuzzle === 'shop'" class="puzzle-section shop-puzzle">
      <h2>🛒 {{ $t('qa.puzzleShopTitle') }}</h2>
      <p class="puzzle-intro">{{ $t('qa.shopIntro') }}</p>

      <div class="progress-row">
        <span>{{ $t('qa.bugsFound') }} {{ shopBugsFound.length }} / 3</span>
      </div>

      <div class="shop-controls">
        <div class="filter-block">
          <label>{{ $t('qa.category') }}</label>
          <select v-model="shopFilter">
            <option value="">{{ $t('qa.allCategories') }}</option>
            <option value="electronics">{{ $t('qa.catElectronics') }}</option>
            <option value="clothing">{{ $t('qa.catClothing') }}</option>
            <option value="books">{{ $t('qa.catBooks') }}</option>
          </select>
        </div>
        <div class="search-block">
          <label>{{ $t('qa.search') }}</label>
          <input v-model="shopSearch" type="text" :placeholder="$t('qa.searchPlaceholder')" />
        </div>
      </div>

      <div class="bugs-list small">
        <div v-for="i in 3" :key="i" class="bug-slot" :class="{ found: shopBugsFound.includes(i) }">
          {{ shopBugsFound.includes(i) ? getShopBugText(i) : $t('qa.bugHidden') }}
        </div>
      </div>

      <ul class="product-list">
        <li v-for="p in displayedProducts" :key="p.id" class="product-item">
          <span class="product-name">{{ p.name }}</span>
          <span class="product-cat">{{ getCategoryLabel(p.category) }}</span>
          <span class="product-price">{{ p.price }} ₽</span>
        </li>
      </ul>
      <p v-if="displayedProducts.length === 0" class="no-results">{{ $t('qa.noProducts') }}</p>

      <div v-if="shopBugsFound.length === 3" class="surprise-msg">🎊 {{ $t('qa.allBugsFound') }}</div>
    </section>

    <div class="qa-footer">
      <p>{{ $t('qa.footer') }} 🚀</p>
    </div>
  </div>
</template>

<script>
const STORAGE_TRIANGLE_BUGS = 'qa_triangle_bugs';
const STORAGE_TRIANGLE_CASES = 'qa_triangle_cases';
const STORAGE_SHOP_BUGS = 'qa_shop_bugs';

// Правильная логика типа треугольника (для сравнения)
function correctTriangleType(a, b, c) {
  const x = Number(a);
  const y = Number(b);
  const z = Number(c);
  if (isNaN(x) || isNaN(y) || isNaN(z)) return 'invalid';
  if (x <= 0 || y <= 0 || z <= 0) return 'invalid';
  if (x + y <= z || x + z <= y || y + z <= x) return 'invalid';
  if (x === y && y === z) return 'equilateral';
  if (x === y || y === z || x === z) return 'isosceles';
  return 'scalene';
}

// БАГИ: 1) ноль не проверяется — (0,1,1) даёт тип; 2) отрицательные — (-1,2,2) считаются через Math.abs; 3) (1,1,1) равносторонний возвращается как равнобедренный; 4) (2,2,3) равнобедренный возвращается как разносторонний
function buggyTriangleType(a, b, c) {
  const x = Number(a);
  const y = Number(b);
  const z = Number(c);
  if (isNaN(x) || isNaN(y) || isNaN(z)) return { type: 'invalid', bug: null };
  if (x + y < z || x + z < y || y + z < x) return { type: 'invalid', bug: null };
  const u = Math.abs(x);
  const v = Math.abs(y);
  const w = Math.abs(z);
  if (u === v && u === w) return { type: 'isosceles', bug: 3 };
  if (u === v || v === w || u === w) return { type: 'scalene', bug: 4 };
  return { type: 'scalene', bug: null };
}

function detectTriangleBugs(a, b, c, buggyResult) {
  const x = Number(a);
  const y = Number(b);
  const z = Number(c);
  const bugs = [];
  if (x === 0 || y === 0 || z === 0) {
    if (buggyResult.type !== 'invalid') bugs.push(1);
  }
  if (x < 0 || y < 0 || z < 0) {
    if (buggyResult.type !== 'invalid') bugs.push(2);
  }
  if (buggyResult.bug) bugs.push(buggyResult.bug);
  return bugs;
}

function getCaseKey(a, b, c) {
  const type = correctTriangleType(a, b, c);
  const x = Number(a);
  const y = Number(b);
  const z = Number(c);
  if (type === 'invalid') {
    if (x < 0 || y < 0 || z < 0) return 'invalid_neg';
    if (x <= 0 || y <= 0 || z <= 0) return 'invalid_zero';
    return 'invalid_inequality';
  }
  return type;
}

const PRODUCTS = [
  { id: 1, name: 'Смартфон', category: 'electronics', price: 29900 },
  { id: 2, name: 'Наушники', category: 'electronics', price: 3990 },
  { id: 3, name: 'Футболка', category: 'clothing', price: 1290 },
  { id: 4, name: 'Куртка', category: 'clothing', price: 5990 },
  { id: 5, name: 'Книга Python', category: 'books', price: 890 },
  { id: 6, name: 'Книга JavaScript', category: 'books', price: 990 },
];

export default {
  name: 'QAPractice',
  data() {
    return {
      currentPuzzle: null,
      qaLink: typeof window !== 'undefined' ? window.location.origin + '/qa' : '/qa',
      triangle: { a: '', b: '', c: '' },
      triangleResult: null,
      triangleResultIsBug: false,
      triangleBugsFound: this.loadJson(STORAGE_TRIANGLE_BUGS) || [],
      triangleCasesTried: new Set(this.loadJson(STORAGE_TRIANGLE_CASES) || []),
      shopFilter: '',
      shopSearch: '',
      shopBugsFound: this.loadJson(STORAGE_SHOP_BUGS) || [],
      products: PRODUCTS,
    };
  },
  computed: {
    displayedProducts() {
      let list = [...this.products];
      if (this.shopFilter === 'clothing') {
        list = [];
      } else if (this.shopFilter) {
        list = list.filter((p) => p.category === this.shopFilter);
      }
      const q = (this.shopSearch || '').trim();
      if (q) {
        list = list.filter((p) => p.name === q);
      }
      return list;
    },
  },
  watch: {
    shopFilter() {
      this.detectShopBugs();
    },
    shopSearch() {
      this.detectShopBugs();
    },
  },
  methods: {
    loadJson(key) {
      try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    },
    saveJson(key, val) {
      localStorage.setItem(key, JSON.stringify(val));
    },
    checkTriangle() {
      const a = this.triangle.a;
      const b = this.triangle.b;
      const c = this.triangle.c;
      const correct = correctTriangleType(a, b, c);
      const buggy = buggyTriangleType(a, b, c);

      const typeLabels = {
        equilateral: this.$t('qa.typeEquilateral'),
        isosceles: this.$t('qa.typeIsosceles'),
        scalene: this.$t('qa.typeScalene'),
        invalid: this.$t('qa.typeInvalid'),
      };
      this.triangleResult = typeLabels[buggy.type] || buggy.type;
      this.triangleResultIsBug = correct !== buggy.type || (buggy.bug !== null);

      const newBugs = detectTriangleBugs(a, b, c, buggy);
      const prev = [...this.triangleBugsFound];
      newBugs.forEach((id) => {
        if (!prev.includes(id)) prev.push(id);
      });
      prev.sort((x, y) => x - y);
      this.triangleBugsFound = prev;
      this.saveJson(STORAGE_TRIANGLE_BUGS, prev);

      const caseKey = getCaseKey(a, b, c);
      const cases = new Set(this.triangleCasesTried);
      cases.add(caseKey);
      this.triangleCasesTried = cases;
      this.saveJson(STORAGE_TRIANGLE_CASES, [...cases]);
    },
    revealShopBug(id) {
      const next = this.shopBugsFound.includes(id) ? this.shopBugsFound : [...this.shopBugsFound, id];
      this.shopBugsFound = next;
      this.saveJson(STORAGE_SHOP_BUGS, next);
    },
    detectShopBugs() {
      if (this.shopFilter === 'clothing') this.revealShopBug(1);
      const q = (this.shopSearch || '').trim();
      if (!q || this.displayedProducts.length > 0) return;
      const base = this.shopFilter === 'clothing' ? [] : (this.shopFilter ? this.products.filter((p) => p.category === this.shopFilter) : this.products);
      const wouldFindCorrect = base.some((p) => p.name.toLowerCase().includes(q.toLowerCase()));
      const wouldFindBuggy = base.some((p) => p.name.includes(q));
      if (!wouldFindCorrect || wouldFindBuggy) return;
      const exactNameMatch = base.some((p) => p.name.toLowerCase() === q.toLowerCase());
      if (exactNameMatch) this.revealShopBug(3);
      else this.revealShopBug(2);
    },
    getShopBugText(i) {
      const key = ['qa.shopBug1', 'qa.shopBug2', 'qa.shopBug3'][i - 1];
      return this.$t(key);
    },
    getCategoryLabel(cat) {
      const map = { electronics: this.$t('qa.catElectronics'), clothing: this.$t('qa.catClothing'), books: this.$t('qa.catBooks') };
      return map[cat] || cat;
    },
  },
};
</script>

<style scoped>
.qa-practice {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px;
}

.qa-header {
  text-align: center;
  margin-bottom: 28px;
}

.qa-header h1 {
  font-size: 1.75rem;
  color: #333;
  margin-bottom: 8px;
}

.qa-subtitle {
  color: #555;
  font-size: 1.05rem;
  margin-bottom: 12px;
}

.qa-hint {
  font-size: 0.9rem;
  color: #666;
}

.qa-hint code {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 6px;
  word-break: break-all;
}

.puzzles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.puzzle-card {
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.puzzle-card:hover {
  border-color: #667eea;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
}

.puzzle-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 12px;
}

.puzzle-card h2 {
  margin: 0 0 8px;
  font-size: 1.2rem;
  color: #333;
}

.puzzle-card p {
  margin: 0 0 16px;
  color: #555;
  font-size: 0.95rem;
  line-height: 1.4;
}

.puzzle-cta {
  color: #667eea;
  font-weight: 600;
}

.back-btn {
  margin-bottom: 20px;
  padding: 8px 16px;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}

.back-btn:hover {
  background: #e0e0e0;
}

.puzzle-section {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.puzzle-section h2 {
  margin: 0 0 8px;
  font-size: 1.35rem;
  color: #333;
}

.puzzle-intro {
  color: #555;
  font-size: 0.95rem;
  margin-bottom: 20px;
  line-height: 1.5;
}

.progress-row {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  color: #555;
}

.bugs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.bugs-list.small {
  margin-bottom: 16px;
}

.bug-slot {
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #888;
}

.bug-slot.found {
  background: #e8f5e9;
  color: #2e7d32;
}

.triangle-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 220px;
  margin-bottom: 16px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-row label {
  width: 50px;
  font-weight: 500;
}

.input-row input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.submit-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.submit-btn:hover {
  opacity: 0.95;
}

.result-box {
  padding: 14px 18px;
  background: #f0f9ff;
  border: 1px solid #b3e0ff;
  border-radius: 8px;
  margin-top: 12px;
}

.result-box.bug {
  background: #fff3e0;
  border-color: #ffcc80;
}

.bug-found-msg {
  margin: 8px 0 0;
  color: #e65100;
  font-weight: 600;
}

.surprise-msg {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  border-radius: 8px;
  font-weight: 600;
  text-align: center;
}

.shop-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 16px;
}

.filter-block,
.search-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-block select,
.search-block input {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  min-width: 180px;
}

.product-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.product-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  align-items: center;
}

.product-name {
  font-weight: 500;
}

.product-cat {
  color: #666;
  font-size: 0.9rem;
}

.product-price {
  font-weight: 600;
  color: #2e7d32;
}

.no-results {
  color: #888;
  padding: 20px;
}

.qa-footer {
  text-align: center;
  margin-top: 40px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
  color: #555;
}
</style>

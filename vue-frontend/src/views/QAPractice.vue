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
      <div class="puzzle-card" @click="$router.push('/testing-types')">
        <span class="puzzle-icon">🧪</span>
        <h2>{{ $t('qa.puzzleTestingTypesTitle') }}</h2>
        <p>{{ $t('qa.puzzleTestingTypesDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/usability-report')">
        <span class="puzzle-icon">📋</span>
        <h2>{{ $t('qa.puzzleUsabilityReportTitle') }}</h2>
        <p>{{ $t('qa.puzzleUsabilityReportDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/qa/user-story')">
        <span class="puzzle-icon">📝</span>
        <h2>{{ $t('qa.puzzleUserStoryTitle') }}</h2>
        <p>{{ $t('qa.puzzleUserStoryDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/qa/test-plan')">
        <span class="puzzle-icon">📘</span>
        <h2>{{ $t('qa.puzzleTestPlanTitle') }}</h2>
        <p>{{ $t('qa.puzzleTestPlanDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/qa/test-case')">
        <span class="puzzle-icon">🧾</span>
        <h2>{{ $t('qa.puzzleTestCaseTitle') }}</h2>
        <p>{{ $t('qa.puzzleTestCaseDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/qa/sql')">
        <span class="puzzle-icon">🗃️</span>
        <h2>{{ $t('qa.puzzleSqlTitle') }}</h2>
        <p>{{ $t('qa.puzzleSqlDesc') }}</p>
        <span class="puzzle-cta">{{ $t('qa.puzzleStart') }} →</span>
      </div>
      <div class="puzzle-card" @click="$router.push('/new/tests')">
        <span class="puzzle-icon">🧪</span>
        <h2>{{ $t('qa.puzzleAutoTestsTitle') }}</h2>
        <p>{{ $t('qa.puzzleAutoTestsDesc') }}</p>
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
        <span>{{ $t('qa.bugsFound') }} {{ triangleBugsFound.length }} / 12</span>
      </div>

      <div class="bugs-list triangle-bugs-grid">
        <div v-for="i in 12" :key="i" class="bug-slot" :class="{ found: triangleBugsFound.includes(i) }">
          {{ triangleBugsFound.includes(i) ? getTriangleBugText(i) : $t('qa.bugHidden') }}
        </div>
      </div>

      <div class="triangle-form">
        <div class="input-row">
          <label>{{ $t('qa.sideA') }}</label>
          <input v-model.number="triangle.a" type="number" step="any" @input="onTriangleInput" />
        </div>
        <div class="input-row">
          <label>{{ $t('qa.sideB') }}</label>
          <input v-model.number="triangle.b" type="number" step="any" @input="onTriangleInput" />
        </div>
        <div class="input-row">
          <label>{{ $t('qa.sideC') }}</label>
          <input v-model.number="triangle.c" type="number" step="any" @input="onTriangleInput" />
        </div>
      </div>

      <div class="triangle-canvas-wrap">
        <p v-if="!triangleDraw.draw" class="no-draw-msg">{{ triangleDraw.message }}</p>
        <svg
          v-else
          class="triangle-svg"
          :viewBox="triangleDraw.viewBox"
          preserveAspectRatio="xMidYMid meet"
        >
          <polygon
            :points="triangleDraw.pointsStr"
            :fill="triangleDraw.fill"
            stroke="#333"
            stroke-width="2"
          />
          <text v-for="(t, i) in triangleDraw.labels" :key="'l'+i" :x="t.x" :y="t.y" class="triangle-label" text-anchor="middle">{{ t.text }}</text>
          <text v-for="(s, i) in triangleDraw.sideLabels" :key="'s'+i" :x="s.x" :y="s.y" class="triangle-side-label" text-anchor="middle">{{ s.text }}</text>
        </svg>
      </div>
      <p v-if="triangleDraw.typeLabel" class="result-type">Тип: {{ triangleDraw.typeLabel }}</p>

      <div v-if="triangleBugsFound.length === 12" class="surprise-msg">🎊 {{ $t('qa.allBugsFound') }}</div>
    </section>

    <!-- Практикум: Мини-магазин -->
    <section v-if="currentPuzzle === 'shop'" class="puzzle-section shop-puzzle">
      <h2>🛒 {{ $t('qa.puzzleShopTitle') }}</h2>
      <p class="puzzle-intro">{{ $t('qa.shopIntro') }}</p>

      <div class="progress-row">
        <span>{{ $t('qa.bugsFound') }} {{ shopBugsFound.length }} / 20</span>
        <span v-if="cart.length" class="cart-badge">🛒 {{ cartTotalItems }} {{ $t('qa.cartItems') }}</span>
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

      <div class="bugs-list small shop-bugs-grid">
        <div v-for="i in 20" :key="i" class="bug-slot" :class="{ found: shopBugsFound.includes(i) }">
          {{ shopBugsFound.includes(i) ? getShopBugText(i) : $t('qa.bugHidden') }}
        </div>
      </div>

      <ul class="product-list">
        <li v-for="p in displayedProducts" :key="p.id" class="product-item">
          <span class="product-name">{{ p.name }}</span>
          <span class="product-cat">{{ getCategoryLabel(p.category) }}</span>
          <span class="product-price">{{ displayProductPrice(p) }} €</span>
          <button type="button" class="add-cart-btn" @click="addToCart(p)">+ {{ $t('qa.addToCart') }}</button>
        </li>
      </ul>
      <p v-if="displayedProducts.length === 0" class="no-results">{{ $t('qa.noProducts') }}</p>

      <div v-if="cart.length > 0" class="cart-block">
        <h3>🛒 {{ $t('qa.cart') }}</h3>
        <ul class="cart-list">
          <li v-for="(item, idx) in cart" :key="item.id + '-' + idx" class="cart-item">
            <span class="cart-item-name">{{ getProductById(item.productId).name }}</span>
            <input v-model.number="item.quantity" type="number" class="cart-qty" @change="onCartQtyChange" />
            <span class="cart-item-price">{{ cartItemPrice(item) }} €</span>
            <button type="button" class="remove-cart-btn" @click="removeFromCart(idx)">✕</button>
          </li>
        </ul>
        <p class="cart-total">{{ $t('qa.total') }}: <strong>{{ displayedCartTotal }} €</strong></p>
      </div>

      <div v-if="shopBugsFound.length === 20" class="surprise-msg">🎊 {{ $t('qa.allBugsFound') }}</div>
    </section>

    <div class="qa-footer">
      <p>{{ $t('qa.footer') }} 🚀</p>
    </div>
  </div>
</template>

<script>
const STORAGE_TRIANGLE_BUGS = 'qa_triangle_bugs';
const STORAGE_SHOP_BUGS = 'qa_shop_bugs';
const STORAGE_CART = 'qa_shop_cart';

function validTriangle(a, b, c) {
  const x = Number(a), y = Number(b), z = Number(c);
  if (isNaN(x) || isNaN(y) || isNaN(z) || x <= 0 || y <= 0 || z <= 0) return false;
  return x + y > z && x + z > y && y + z > x;
}

function triangleType(a, b, c) {
  const x = Number(a), y = Number(b), z = Number(c);
  if (!validTriangle(a, b, c)) return 'invalid';
  if (x === y && y === z) return 'equilateral';
  if (x === y || y === z || x === z) return 'isosceles';
  return 'scalene';
}

function computeVertices(a, b, c) {
  const x = Number(a), y = Number(b), z = Number(c);
  const ax = 0, ay = 0, bx = z, by = 0;
  const xC = (y * y - x * x + z * z) / (2 * z);
  const yC = Math.sqrt(Math.max(0, y * y - xC * xC));
  return { ax, ay, bx, by, cx: xC, cy: yC };
}

function scaleToViewBox(ax, ay, bx, by, cx, cy, size = 200) {
  const minX = Math.min(ax, bx, cx);
  const maxX = Math.max(ax, bx, cx);
  const minY = Math.min(ay, by, cy);
  const maxY = Math.max(ay, by, cy);
  const w = maxX - minX || 1;
  const h = maxY - minY || 1;
  const scale = (size * 0.85) / Math.max(w, h);
  const pad = size * 0.08;
  const tx = (vx, vy) => [(vx - minX) * scale + pad, (vy - minY) * scale + pad];
  return { scale, minX, minY, tx, viewBox: `0 0 ${size} ${size}` };
}

function getTriangleDraw(a, b, c, typeLabels) {
  const x = Number(a), y = Number(b), z = Number(c);
  const bugs = [];
  let draw = true;
  let message = '';
  let vert = null;
  let viewBox = '0 0 200 200';
  let pointsStr = '';
  let fill = '#b3e5fc';
  let typeLabel = typeLabels.invalid;
  let labels = [];
  let sideLabels = [];
  const la = String(a), lb = String(b), lc = String(c);

  if (a === '' || b === '' || c === '' || isNaN(x) || isNaN(y) || isNaN(z)) {
    return { draw: false, message: 'Введите стороны', typeLabel: '', viewBox, pointsStr: '0,0 0,0 0,0', fill, labels: [], sideLabels: [], bugIds: [] };
  }

  const valid = validTriangle(a, b, c);
  const correctType = triangleType(a, b, c);
  if (valid) typeLabel = typeLabels[correctType];

  if (x === 0 || y === 0 || z === 0) {
    if (valid) { /* impossible */ }
    vert = computeVertices(x || 1, y || 1, z || 1);
    bugs.push(1);
    message = '';
  } else if (x < 0 || y < 0 || z < 0) {
    vert = computeVertices(Math.abs(x), Math.abs(y), Math.abs(z));
    bugs.push(2);
  } else if (!valid && (x + y <= z || x + z <= y || y + z <= x)) {
    vert = computeVertices(x, y, z);
    bugs.push(3);
  } else if (valid && x === 2 && y === 2 && z === 2) {
    draw = false;
    message = 'Не удалось построить';
    bugs.push(4);
  } else if (valid && x === 1 && y === 1 && z === 1) {
    vert = computeVertices(1, 1, 1.15);
    bugs.push(5);
  } else if (valid && x === 2 && y === 2 && z === 3) {
    vert = computeVertices(2, 2, 3.5);
    bugs.push(6);
  } else if (x >= 100 && y >= 100 && z >= 100) {
    vert = computeVertices(x, y, z);
    bugs.push(7);
  } else if (x > 0 && x < 0.5 && y < 0.5 && z < 0.5) {
    vert = computeVertices(x, y, z);
    bugs.push(8);
  } else if (valid) {
    vert = computeVertices(x, y, z);
  }

  if (!vert && draw && (x !== 1 || y !== 1 || z !== 1)) {
    if (valid) vert = computeVertices(x, y, z);
    else { draw = false; message = 'Не треугольник'; }
  }

  if (vert && draw) {
    const isBug7 = x >= 100 && y >= 100 && z >= 100;
    const isBug8 = x > 0 && x < 0.5 && y < 0.5 && z < 0.5;
    if (isBug7) {
      viewBox = '0 0 50 50';
      pointsStr = `${vert.ax},${vert.ay} ${vert.bx},${vert.by} ${vert.cx},${vert.cy}`;
    } else if (isBug8) {
      viewBox = '0 0 200 200';
      pointsStr = `${vert.ax},${vert.ay} ${vert.bx},${vert.by} ${vert.cx},${vert.cy}`;
    } else {
      const s = scaleToViewBox(vert.ax, vert.ay, vert.bx, vert.by, vert.cx, vert.cy);
      const [pax, pay] = s.tx(vert.ax, vert.ay);
      const [pbx, pby] = s.tx(vert.bx, vert.by);
      const [pcx, pcy] = s.tx(vert.cx, vert.cy);
      pointsStr = `${pax},${pay} ${pbx},${pby} ${pcx},${pcy}`;
      viewBox = s.viewBox;
    }

    const s = !isBug7 && !isBug8 ? scaleToViewBox(vert.ax, vert.ay, vert.bx, vert.by, vert.cx, vert.cy) : null;
    const pax = s ? s.tx(vert.ax, vert.ay)[0] : vert.ax;
    const pay = s ? s.tx(vert.ax, vert.ay)[1] : vert.ay;
    const pbx = s ? s.tx(vert.bx, vert.by)[0] : vert.bx;
    const pby = s ? s.tx(vert.bx, vert.by)[1] : vert.by;
    const pcx = s ? s.tx(vert.cx, vert.cy)[0] : vert.cx;
    const pcy = s ? s.tx(vert.cx, vert.cy)[1] : vert.cy;

    const swapAB = valid && x === 3 && y === 4 && z === 5;
    if (swapAB) bugs.push(9);
    labels = [
      { text: swapAB ? 'B' : 'A', x: pax - 12, y: pay - 8 },
      { text: swapAB ? 'A' : 'B', x: pbx + 12, y: pby - 8 },
      { text: 'C', x: pcx, y: pcy + 16 },
    ];

    const wrongSides = valid && x === 5 && y === 5 && z === 5;
    if (wrongSides) bugs.push(10);
    const midAB = [(pax + pbx) / 2, (pay + pby) / 2];
    const midBC = [(pbx + pcx) / 2, (pby + pcy) / 2];
    const midCA = [(pcx + pax) / 2, (pcy + pay) / 2];
    sideLabels = wrongSides
      ? [{ text: la, x: midAB[0], y: midAB[1] + 14 }, { text: lc, x: midBC[0], y: midBC[1] + 14 }, { text: lb, x: midCA[0], y: midCA[1] + 14 }]
      : [{ text: lc, x: midAB[0], y: midAB[1] + 14 }, { text: la, x: midBC[0], y: midBC[1] + 14 }, { text: lb, x: midCA[0], y: midCA[1] + 14 }];

    if (correctType === 'equilateral' && x === 1 && y === 1 && z === 1 && vert) {
      fill = '#ffcdd2';
      bugs.push(11);
    }
    if (correctType === 'scalene' && x === 3 && y === 4 && z === 5) {
      const pcyFlipped = pay + pby - pcy;
      pointsStr = `${pax},${pay} ${pbx},${pby} ${pcx},${pcyFlipped}`;
      bugs.push(12);
    }
  }

  return { draw: !!vert && draw, message: message || (valid ? '' : 'Не треугольник'), typeLabel, viewBox, pointsStr: pointsStr || '0,0 0,0 0,0', fill, labels, sideLabels, bugIds: bugs };
}

const PRODUCTS = [
  { id: 1, name: 'Смартфон', category: 'electronics', price: 299 },
  { id: 2, name: 'Наушники', category: 'electronics', price: 39.9 },
  { id: 3, name: 'Футболка', category: 'clothing', price: 12.9 },
  { id: 4, name: 'Куртка', category: 'clothing', price: 59.9 },
  { id: 5, name: 'Книга Python', category: 'books', price: 8.9 },
  { id: 6, name: 'Книга JavaScript', category: 'books', price: 9.9 },
];

export default {
  name: 'QAPractice',
  data() {
    return {
      currentPuzzle: null,
      qaLink: typeof window !== 'undefined' ? window.location.origin + '/qa' : '/qa',
      triangle: { a: '', b: '', c: '' },
      triangleBugsFound: this.loadJson(STORAGE_TRIANGLE_BUGS) || [],
      shopFilter: '',
      shopSearch: '',
      shopBugsFound: this.loadJson(STORAGE_SHOP_BUGS) || [],
      products: PRODUCTS,
      cart: this.loadJson(STORAGE_CART) || [],
    };
  },
  computed: {
    typeLabels() {
      return {
        equilateral: this.$t('qa.typeEquilateral'),
        isosceles: this.$t('qa.typeIsosceles'),
        scalene: this.$t('qa.typeScalene'),
        invalid: this.$t('qa.typeInvalid'),
      };
    },
    triangleDraw() {
      return getTriangleDraw(this.triangle.a, this.triangle.b, this.triangle.c, this.typeLabels);
    },
    displayedProducts() {
      let list = [...this.products];
      if (this.shopFilter === 'clothing') list = [];
      else if (this.shopFilter === 'books') {
        list = list.filter((p) => p.category === 'books');
        if (!(this.shopSearch || '').trim()) list = [];
        else if (list.length > 0) {
          const wrong = this.products.find((p) => p.category !== 'books');
          if (wrong) list = [wrong, ...list];
        }
      } else if (this.shopFilter === 'electronics') {
        list = list.filter((p) => p.category === 'electronics');
        list = [...list].reverse();
      } else if (this.shopFilter) list = list.filter((p) => p.category === this.shopFilter);
      const q = (this.shopSearch || '').trim();
      if (q) list = list.filter((p) => p.name === q);
      return list;
    },
    cartTotalItems() {
      if (this.cart.length > 0) return this.cart.length + 1;
      return this.cart.length;
    },
    cartTotal() {
      if (this.cart.length === 0) return 99;
      let t = 0;
      this.cart.forEach((item, idx) => {
        const p = this.products.find((pr) => pr.id === item.productId);
        const qty = (item.quantity === '' || isNaN(Number(item.quantity))) ? 0 : Number(item.quantity);
        if (p) t += p.price * (idx === this.cart.length - 1 ? 1 : qty);
      });
      return t;
    },
    displayedCartTotal() {
      const raw = this.cartTotal;
      if (this.cart.length === 0) return raw;
      return Math.round(raw);
    },
  },
  watch: {
    'triangle.a'() { this.applyTriangleBugsFromDraw(); },
    'triangle.b'() { this.applyTriangleBugsFromDraw(); },
    'triangle.c'() { this.applyTriangleBugsFromDraw(); },
    shopFilter() {
      if (this.shopFilter === 'clothing') this.revealShopBug(1);
      if (this.shopFilter === 'electronics' && this.displayedProducts.length > 0) this.revealShopBug(13);
      if (this.shopFilter === 'books') {
        if (this.displayedProducts.length > 1) this.revealShopBug(12);
        if (!(this.shopSearch || '').trim()) this.revealShopBug(20);
      }
      if ((this.shopFilter || (this.shopSearch || '').trim()) && this.displayedProducts.some((p) => p.id === 2)) this.revealShopBug(11);
      this.detectShopSearchBugs((this.shopSearch || '').trim(), this.displayedProducts);
    },
    shopSearch() {
      this.detectShopSearchBugs((this.shopSearch || '').trim(), this.displayedProducts);
      if (this.shopFilter === 'electronics' && this.displayedProducts.length > 1) this.revealShopBug(13);
      if (this.shopFilter === 'books' && !(this.shopSearch || '').trim()) this.revealShopBug(20);
      if ((this.shopFilter || (this.shopSearch || '').trim()) && this.displayedProducts.some((p) => p.id === 2)) this.revealShopBug(11);
    },
    cart: { deep: true, handler() { this.saveJson(STORAGE_CART, this.cart); this.detectShopCartBugs(); } },
  },
  methods: {
    loadJson(key) {
      try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
      } catch { return null; }
    },
    saveJson(key, val) {
      localStorage.setItem(key, JSON.stringify(val));
    },
    onTriangleInput() {
      const a = this.triangle.a, b = this.triangle.b, c = this.triangle.c;
      const out = getTriangleDraw(a, b, c, this.typeLabels);
      this.applyTriangleBugs(out.bugIds || []);
    },
    applyTriangleBugs(ids) {
      const prev = [...this.triangleBugsFound];
      ids.forEach((id) => { if (!prev.includes(id)) prev.push(id); });
      prev.sort((x, y) => x - y);
      this.triangleBugsFound = prev;
      this.saveJson(STORAGE_TRIANGLE_BUGS, prev);
    },
    getTriangleBugText(i) {
      return this.$t('qa.triangleBug' + i);
    },
    revealShopBug(id) {
      if (this.shopBugsFound.includes(id)) return;
      this.shopBugsFound = [...this.shopBugsFound, id];
      this.saveJson(STORAGE_SHOP_BUGS, this.shopBugsFound);
    },
    detectShopSearchBugs(q, list) {
      if (!q || list.length > 0) return;
      const base = this.shopFilter === 'clothing' ? [] : (this.shopFilter ? this.products.filter((p) => p.category === this.shopFilter) : this.products);
      const exactMatch = base.some((p) => p.name === q);
      const exactMatchIgnoreCase = base.some((p) => p.name.toLowerCase() === q.toLowerCase());
      const wouldFindPartial = base.some((p) => p.name.toLowerCase().includes(q.toLowerCase()));
      if (!wouldFindPartial) return;
      if (exactMatch) return;
      if (exactMatchIgnoreCase) this.revealShopBug(3);
      else this.revealShopBug(2);
    },
    getProductById(id) {
      if (id === 2) return this.products.find((p) => p.id === 1) || this.products[0] || { name: '?', price: 0 };
      return this.products.find((p) => p.id === id) || { name: '?', price: 0 };
    },
    displayProductPrice(p) {
      if (p.id === 2) return Math.floor(p.price);
      return p.price;
    },
    cartItemPrice(item) {
      const p = this.getProductById(item.productId);
      const q = (item.quantity === '' || isNaN(Number(item.quantity))) ? 0 : Number(item.quantity);
      return p.price * q;
    },
    addToCart(p) {
      const list = this.displayedProducts;
      const idx = list.findIndex((d) => d.id === p.id);
      const idToAdd = (idx === 1 && list.length >= 2) ? list[0].id : p.id;
      this.cart.push({ productId: idToAdd, quantity: 1 });
      if (this.cart.filter((i) => i.productId === idToAdd).length >= 3) this.revealShopBug(4);
    },
    removeFromCart(idx) {
      if (idx === 0 && this.cart.length > 1) {
        this.cart.splice(1, 1);
        this.revealShopBug(5);
      } else if (idx === 1 && this.cart.length >= 2) {
        this.cart.splice(0, 1);
        this.revealShopBug(15);
      } else {
        this.cart.splice(idx, 1);
      }
    },
    onCartQtyChange() {
      const hasZero = this.cart.some((i) => i.quantity < 1 || i.quantity === '' || isNaN(Number(i.quantity)));
      if (hasZero) this.revealShopBug(6);
      let expected = 0;
      this.cart.forEach((item, idx) => {
        const p = this.products.find((pr) => pr.id === item.productId);
        const qty = (item.quantity === '' || isNaN(Number(item.quantity))) ? 0 : Number(item.quantity);
        if (p) expected += p.price * (idx === this.cart.length - 1 ? 1 : qty);
      });
      if (this.cart.length >= 2 && expected !== this.displayedCartTotal) this.revealShopBug(7);
    },
    detectShopCartBugs() {
      let expected = 0;
      let hasNegative = false;
      this.cart.forEach((item, idx) => {
        const p = this.products.find((pr) => pr.id === item.productId);
        const qty = (item.quantity === '' || isNaN(Number(item.quantity))) ? 0 : Number(item.quantity);
        if (qty < 0) hasNegative = true;
        if (p) expected += p.price * (idx === this.cart.length - 1 ? 1 : qty);
      });
      if (hasNegative) this.revealShopBug(16);
      if (this.cart.length >= 2 && expected !== Math.round(expected)) this.revealShopBug(17);
      if (this.cart.length >= 2 && this.cartTotal !== expected) this.revealShopBug(8);
      if (this.cart.length === 0 && this.cartTotal > 0) this.revealShopBug(9);
      const realCount = this.cart.reduce((s, i) => s + (i.quantity || 0), 0);
      if (this.cart.length >= 2 && realCount > 0 && this.cartTotalItems !== realCount) this.revealShopBug(10);
      if (this.cart.length === 2) this.revealShopBug(19);
      const list = this.displayedProducts;
      if (this.cart.length >= 2 && list.length >= 2 && this.cart.some((i) => i.productId === list[0].id) && this.cart.some((i) => i.productId === list[1].id)) this.revealShopBug(14);
      if (this.cart.some((i) => i.productId === 2)) this.revealShopBug(18);
    },
    getShopBugText(i) {
      return this.$t('qa.shopBug' + i);
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

.triangle-bugs-grid { max-width: 100%; }
.shop-bugs-grid { max-width: 100%; }

.triangle-canvas-wrap {
  margin: 20px 0;
  min-height: 220px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.triangle-svg {
  width: 100%;
  max-width: 280px;
  height: 220px;
}

.triangle-label, .triangle-side-label {
  font-size: 14px;
  fill: #333;
}
.triangle-side-label { font-size: 12px; fill: #555; }

.no-draw-msg {
  color: #666;
  padding: 20px;
}

.result-type {
  font-weight: 600;
  color: #333;
  margin-top: 8px;
}

.cart-badge { margin-left: auto; }

.add-cart-btn {
  padding: 6px 12px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.cart-block {
  margin-top: 24px;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.cart-block h3 { margin: 0 0 12px; font-size: 1.1rem; }

.cart-list { list-style: none; padding: 0; margin: 0 0 12px; }

.cart-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.cart-item-name { flex: 1; }
.cart-qty { width: 56px; padding: 4px; text-align: center; }
.cart-item-price { min-width: 80px; text-align: right; }
.remove-cart-btn {
  padding: 4px 10px;
  background: #e74c3c;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cart-total { margin: 0; font-size: 1.1rem; }

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

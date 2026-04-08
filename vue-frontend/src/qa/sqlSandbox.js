/**
 * QA SQL-тренажёр: SQLite в браузере (sql.js), схема интернет-магазина, уроки с проверкой результата.
 */

function esc(s) {
  return String(s).replace(/'/g, "''");
}

const CUSTOMER_NAMES = [
  'Анна Смирнова',
  'Борис Козлов',
  'Вера Орлова',
  'Глеб Волков',
  'Дарья Новикова',
  'Егор Морозов',
  'Жанна Лебедева',
  'Илья Соколов',
  'Ксения Павлова',
  'Леонид Семёнов',
  'Марина Егорова',
  'Никита Андреев',
];

/** Города покупателей — европейские (значения в БД на латинице, как в международных демо-данных). */
const CITIES = ['Berlin', 'Amsterdam', 'Prague', 'Vienna', 'Lisbon'];

const PRODUCT_DATA = [
  ['SKU-E01', 'Наушники Bluetooth', 'Электроника', 499000, 40],
  ['SKU-E02', 'Клавиатура механическая', 'Электроника', 890000, 22],
  ['SKU-E03', 'USB-хаб 7 портов', 'Электроника', 129000, 100],
  ['SKU-H01', 'Кружка керамическая', 'Дом', 45000, 200],
  ['SKU-H02', 'Набор полотенец', 'Дом', 120000, 55],
  ['SKU-H03', 'Коврик придверный', 'Дом', 29000, 80],
  ['SKU-B01', 'SQL для практиков', 'Книги', 99000, 60],
  ['SKU-B02', 'Агильные ритуалы', 'Книги', 76000, 35],
  ['SKU-S01', 'Мяч футбольный', 'Спорт', 210000, 30],
  ['SKU-S02', 'Бутылка 750 мл', 'Спорт', 89000, 90],
  ['SKU-S03', 'Скакалка', 'Спорт', 15000, 120],
  ['SKU-E04', 'Мышь беспроводная', 'Электроника', 159000, 70],
];

const ORDER_STATUSES = ['paid', 'pending', 'shipped', 'cancelled'];

function buildCustomers() {
  return CUSTOMER_NAMES.map((full_name, i) => {
    const id = i + 1;
    const m = String((i % 12) + 1).padStart(2, '0');
    const d = String((i % 27) + 1).padStart(2, '0');
    return {
      id,
      full_name,
      email: `user${id}@shop.demo`,
      city: CITIES[i % CITIES.length],
      signup_date: `2024-${m}-${d}`,
    };
  });
}

function buildProducts() {
  return PRODUCT_DATA.map((row, i) => ({
    id: i + 1,
    sku: row[0],
    name: row[1],
    category: row[2],
    price_cents: row[3],
    stock_qty: row[4],
  }));
}

function buildOrders(customersCount) {
  const rows = [];
  for (let id = 1; id <= 18; id++) {
    const customer_id = ((id - 1) % customersCount) + 1;
    const m = String((id % 11) + 1).padStart(2, '0');
    const d = String((id % 26) + 1).padStart(2, '0');
    rows.push({
      id,
      customer_id,
      order_date: `2025-${m}-${d}`,
      status: ORDER_STATUSES[id % ORDER_STATUSES.length],
      total_cents: 0,
    });
  }
  return rows;
}

function buildOrderItems(orders, products) {
  const rows = [];
  let id = 1;
  for (const o of orders) {
    const nItems = 1 + (o.id % 3);
    for (let j = 0; j < nItems; j++) {
      const product_id = ((o.id + j - 1) % products.length) + 1;
      const p = products[product_id - 1];
      const quantity = 1 + ((o.id + j) % 4);
      const unit_price_cents = p.price_cents;
      const line_total_cents = quantity * unit_price_cents;
      rows.push({
        id,
        order_id: o.id,
        product_id,
        quantity,
        unit_price_cents,
        line_total_cents,
      });
      id += 1;
    }
  }
  return rows;
}

function ordersWithTotals(orders, orderItems) {
  const byOrder = {};
  for (const oi of orderItems) {
    byOrder[oi.order_id] = (byOrder[oi.order_id] || 0) + oi.line_total_cents;
  }
  return orders.map((o) => ({ ...o, total_cents: byOrder[o.id] || 0 }));
}

/**
 * SQL создания и заполнения: customers, products, orders, order_items.
 */
export function getSeedSQL() {
  const customers = buildCustomers();
  const products = buildProducts();
  let orders = buildOrders(customers.length);
  const orderItems = buildOrderItems(orders, products);
  orders = ordersWithTotals(orders, orderItems);

  const cCols = '(id, full_name, email, city, signup_date)';
  const cVals = customers
    .map(
      (r) =>
        `(${r.id}, '${esc(r.full_name)}', '${esc(r.email)}', '${esc(r.city)}', '${r.signup_date}')`,
    )
    .join(',\n');

  const pCols = '(id, sku, name, category, price_cents, stock_qty)';
  const pVals = products
    .map(
      (r) =>
        `(${r.id}, '${esc(r.sku)}', '${esc(r.name)}', '${esc(r.category)}', ${r.price_cents}, ${r.stock_qty})`,
    )
    .join(',\n');

  const oCols = '(id, customer_id, order_date, status, total_cents)';
  const oVals = orders
    .map(
      (r) =>
        `(${r.id}, ${r.customer_id}, '${r.order_date}', '${r.status}', ${r.total_cents})`,
    )
    .join(',\n');

  const oiCols = '(id, order_id, product_id, quantity, unit_price_cents, line_total_cents)';
  const oiVals = orderItems
    .map(
      (r) =>
        `(${r.id}, ${r.order_id}, ${r.product_id}, ${r.quantity}, ${r.unit_price_cents}, ${r.line_total_cents})`,
    )
    .join(',\n');

  return `
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  full_name TEXT NOT NULL,
  email TEXT,
  city TEXT,
  signup_date TEXT
);

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL,
  name TEXT,
  category TEXT,
  price_cents INTEGER,
  stock_qty INTEGER
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  order_date TEXT,
  status TEXT,
  total_cents INTEGER,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER,
  unit_price_cents INTEGER,
  line_total_cents INTEGER,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO customers ${cCols} VALUES
${cVals};

INSERT INTO products ${pCols} VALUES
${pVals};

INSERT INTO orders ${oCols} VALUES
${oVals};

INSERT INTO order_items ${oiCols} VALUES
${oiVals};
`.trim();
}

/** Сравнимое представление ячейки: числа/строки с числом приводятся к одному виду. */
export function normalizeCellForCompare(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) return String(v);
    if (Number.isInteger(v)) return String(v);
    const r = Math.round(v);
    if (Math.abs(v - r) < 1e-9) return String(r);
    return String(v);
  }
  if (typeof v === 'boolean') return v ? '1' : '0';
  const s = String(v).trim();
  if (s === '') return '';
  if (/^-?\d+$/.test(s)) return s;
  if (/^-?\d+\.\d+$/.test(s)) {
    const num = Number(s);
    if (Number.isFinite(num)) {
      const r = Math.round(num);
      if (Math.abs(num - r) < 1e-9) return String(r);
    }
  }
  return s;
}

/** Макс. число колонок для перебора перестановок (n!); дальше только сравнение по именам колонок. */
const GRIDS_MAX_PERMUTE_COLS = 8;

/** Все перестановки индексов [0..n-1] (n ≤ 8). */
function forEachColumnPermutation(n, fn) {
  const arr = Array.from({ length: n }, (_, i) => i);
  function dfs(start) {
    if (start === n) {
      fn([...arr]);
      return;
    }
    for (let i = start; i < n; i++) {
      const tmp = arr[start];
      arr[start] = arr[i];
      arr[i] = tmp;
      dfs(start + 1);
      const t2 = arr[start];
      arr[start] = arr[i];
      arr[i] = t2;
    }
  }
  dfs(0);
}

/**
 * Тот же набор строк, что у эталона, если переупорядочить колонки ответа пользователя.
 * Нужен, когда совпадают данные, но другие имена/порядок колонок (разный SQL).
 */
function gridsMatchByColumnPermutation(userCols, userRows, refCols, refRows) {
  const n = userCols && userCols.length;
  if (!n || n !== (refCols && refCols.length)) return false;
  const ur = userRows || [];
  const rr = refRows || [];
  if (ur.length !== rr.length) return false;
  if (n > GRIDS_MAX_PERMUTE_COLS) return false;

  const refSigs = rr
    .map((row) => refCols.map((_, i) => normalizeCellForCompare(row[i])).join('\u001f'))
    .sort();

  let matched = false;
  forEachColumnPermutation(n, (perm) => {
    if (matched) return;
    const userSigs = ur
      .map((row) => perm.map((ui) => normalizeCellForCompare(row[ui])).join('\u001f'))
      .sort();
    if (userSigs.length !== refSigs.length) return;
    matched = userSigs.every((s, idx) => s === refSigs[idx]);
  });
  return matched;
}

/** Последний результат SELECT из exec (многострочный SQL). */
export function getLastSelectResult(db, sql) {
  const results = db.exec(sql);
  if (!results || !results.length) {
    return null;
  }
  for (let i = results.length - 1; i >= 0; i--) {
    const block = results[i];
    if (block.columns && block.columns.length) {
      return {
        columns: block.columns,
        rows: block.values || [],
      };
    }
  }
  return null;
}

/**
 * Нормализация для сравнения: порядок колонок по имени (lower), строки как отсортированные сигнатуры.
 */
export function normalizeGrid(columns, rows) {
  if (!columns || !columns.length) {
    return { colKeys: [], rowSigs: [] };
  }
  const order = columns
    .map((c, i) => ({ key: String(c).toLowerCase(), i }))
    .sort((a, b) => a.key.localeCompare(b.key));
  const colKeys = order.map((o) => o.key);
  const rowSigs = (rows || []).map((row) =>
    order.map((o) => normalizeCellForCompare(row[o.i])).join('\u001f'),
  );
  rowSigs.sort();
  return { colKeys, rowSigs };
}

export function gridsMatch(columnsA, rowsA, columnsB, rowsB) {
  const a = normalizeGrid(columnsA, rowsA);
  const b = normalizeGrid(columnsB, rowsB);
  if (a.colKeys.length !== b.colKeys.length) return false;
  for (let i = 0; i < a.colKeys.length; i++) {
    if (a.colKeys[i] !== b.colKeys[i]) return false;
  }
  if (a.rowSigs.length !== b.rowSigs.length) return false;
  for (let i = 0; i < a.rowSigs.length; i++) {
    if (a.rowSigs[i] !== b.rowSigs[i]) return false;
  }
  return true;
}

/**
 * Эталонные колонки есть в ответе пользователя (например SELECT * vs SELECT id, name):
 * проецируем строки пользователя на имена/порядок эталона и сравниваем.
 */
function gridsMatchUserSupersetColumns(columnsUser, rowsUser, columnsRef, rowsRef) {
  if (!columnsRef?.length || !columnsUser?.length) return false;
  if (columnsUser.length < columnsRef.length) return false;
  const idxs = columnsRef.map((rc) =>
    columnsUser.findIndex((uc) => String(uc).toLowerCase() === String(rc).toLowerCase()),
  );
  if (idxs.some((i) => i < 0)) return false;
  const projectedRows = (rowsUser || []).map((row) => idxs.map((i) => row[i]));
  return gridsMatch(columnsRef, projectedRows, columnsRef, rowsRef);
}

/**
 * Сравнение результатов SELECT: сначала по именам колонок (порядок строк/колонок не важен),
 * иначе та же таблица значений при какой-то перестановке колонок ответа пользователя,
 * иначе ответ с лишними колонками (SELECT *), если в нём есть все колонки эталона по имени.
 */
export function gridsMatchRelaxed(columnsUser, rowsUser, columnsRef, rowsRef) {
  if (gridsMatch(columnsUser, rowsUser, columnsRef, rowsRef)) return true;
  if (gridsMatchByColumnPermutation(columnsUser, rowsUser, columnsRef, rowsRef)) return true;
  if (gridsMatchUserSupersetColumns(columnsUser, rowsUser, columnsRef, rowsRef)) return true;
  return false;
}

/**
 * Проверка задания: эталонный SELECT на копии сида и результат пользователя на другой копии.
 * @returns {{ ok: boolean, userError?: string, messageKey?: string }}
 */
export function validateTaskWithCtor(SQL, seedUint8Array, userSql, checkSql) {
  if (!SQL || !seedUint8Array || !seedUint8Array.byteLength) {
    return { ok: false, userError: 'internal' };
  }

  let dbUser;
  let userResult;
  try {
    dbUser = new SQL.Database(seedUint8Array);
    userResult = getLastSelectResult(dbUser, userSql);
  } catch (e) {
    return { ok: false, userError: e.message || String(e) };
  } finally {
    try {
      if (dbUser) dbUser.close();
    } catch (_) {
      /* ignore */
    }
  }

  if (!userResult) {
    return { ok: false, messageKey: 'qa.sqlWrongNoSelect' };
  }

  let dbRef;
  let refResult;
  try {
    dbRef = new SQL.Database(seedUint8Array);
    refResult = getLastSelectResult(dbRef, checkSql);
  } catch (e) {
    return { ok: false, userError: e.message || String(e) };
  } finally {
    try {
      if (dbRef) dbRef.close();
    } catch (_) {
      /* ignore */
    }
  }

  if (!refResult) {
    return { ok: false, userError: 'internal: bad check sql' };
  }

  const ok = gridsMatchRelaxed(
    userResult.columns,
    userResult.rows,
    refResult.columns,
    refResult.rows,
  );
  if (!ok) {
    return { ok: false, messageKey: 'qa.sqlWrongResult' };
  }
  return { ok: true };
}

/** Урок с подзаданиями; checkSql — эталон для набора строк/значений (другой SQL с тем же результатом тоже засчитывается; SELECT * допустим, если в выборке есть все колонки эталона по имени). */
export const SQL_LESSONS = [
  {
    id: 'l01',
    title: 'Таблицы и первый SELECT',
    theory:
      'Данные интернет-магазина: покупатели (customers), товары (products), заказы (orders) и позиции заказа (order_items). Имена таблиц в SQL — латиницей, как на вкладках превью справа. SELECT читает строки; * — все колонки. Запросы выполняются только в браузере. Порядок строк в ответе для проверки не важен, если в задании не сказано иное.',
    tasks: [
      {
        id: 'l01-t1',
        hint: 'Таблица customers. Вывести: все колонки всех строк (SELECT *). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT * FROM customers;',
        checkSql: 'SELECT * FROM customers;',
      },
      {
        id: 'l01-t2',
        hint: 'Таблица products. Вывести: все колонки всех строк (SELECT *). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT * FROM products;',
        checkSql: 'SELECT * FROM products;',
      },
      {
        id: 'l01-t3',
        hint: 'Таблица orders. Вывести: все колонки всех строк (SELECT *). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT * FROM orders;',
        checkSql: 'SELECT * FROM orders;',
      },
      {
        id: 'l01-t4',
        hint: 'Таблица order_items. Вывести: все колонки всех строк (SELECT *). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT * FROM order_items;',
        checkSql: 'SELECT * FROM order_items;',
      },
    ],
  },
  {
    id: 'l02',
    title: 'Выбор колонок',
    theory:
      'Вместо * перечисляют нужные поля через запятую. В подсказке к заданию указаны колонки для вывода и что не нужно (WHERE, GROUP BY, ORDER BY). Имена полей — как в схеме таблицы.',
    tasks: [
      {
        id: 'l02-t1',
        hint: 'Таблица customers. Вывести колонки: full_name, email, city. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT full_name, email, city FROM customers;',
        checkSql: 'SELECT full_name, email, city FROM customers;',
      },
      {
        id: 'l02-t2',
        hint: 'Таблица products. Вывести колонки: sku, name, price_cents. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT sku, name, price_cents FROM products;',
        checkSql: 'SELECT sku, name, price_cents FROM products;',
      },
      {
        id: 'l02-t3',
        hint: 'Таблица orders. Вывести колонки: id, order_date, status. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT id, order_date, status FROM orders;',
        checkSql: 'SELECT id, order_date, status FROM orders;',
      },
      {
        id: 'l02-t4',
        hint: 'Таблица order_items. Вывести колонки: order_id, product_id, quantity. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT order_id, product_id, quantity FROM order_items;',
        checkSql: 'SELECT order_id, product_id, quantity FROM order_items;',
      },
    ],
  },
  {
    id: 'l03',
    title: 'WHERE: фильтр строк',
    theory:
      'WHERE оставляет только строки, для которых условие истинно. Строковые значения из базы (категории, города, статусы) берите в кавычках точно как в данных: категории часто на русском («Электроника»), города в демо — латиницей (Berlin, Prague). Числа — без кавычек. Каждое задание ссылается на таблицу products, orders, customers или order_items.',
    tasks: [
      {
        id: 'l03-t1',
        hint: "Таблица products. Вывести: все колонки (*). Фильтр WHERE: category = 'Электроника'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT * FROM products WHERE category = 'Электроника';",
        checkSql:
          "SELECT * FROM products WHERE category = 'Электроника';",
      },
      {
        id: 'l03-t2',
        hint: "Таблица orders. Вывести: все колонки (*). Фильтр WHERE: status = 'paid'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT * FROM orders WHERE status = 'paid';",
        checkSql: "SELECT * FROM orders WHERE status = 'paid';",
      },
      {
        id: 'l03-t3',
        hint: "Таблица customers. Вывести колонки: full_name, email. Фильтр WHERE: city = 'Berlin'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT full_name, email FROM customers WHERE city = 'Berlin';",
        checkSql:
          "SELECT full_name, email FROM customers WHERE city = 'Berlin';",
      },
      {
        id: 'l03-t4',
        hint: 'Таблица order_items. Вывести: все колонки (*). Фильтр WHERE: quantity >= 3. Без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT * FROM order_items WHERE quantity >= 3;',
        checkSql: 'SELECT * FROM order_items WHERE quantity >= 3;',
      },
    ],
  },
  {
    id: 'l04',
    title: 'AND, OR и IN',
    theory:
      'AND и OR объединяют условия. IN (список) удобен, когда поле должно быть одним из нескольких значений. В подсказках к заданиям указана нужная таблица.',
    tasks: [
      {
        id: 'l04-t1',
        hint: "Таблица products. Вывести колонки: name, category. Фильтр WHERE: category IN ('Книги', 'Спорт'). Без GROUP BY, без ORDER BY.",
        exampleSql:
          "SELECT name, category FROM products WHERE category IN ('Книги', 'Спорт');",
        checkSql:
          "SELECT name, category FROM products WHERE category IN ('Книги', 'Спорт');",
      },
      {
        id: 'l04-t2',
        hint: "Таблица orders. Вывести колонки: id, status. Фильтр WHERE: status IN ('pending', 'shipped') (допустим и эквивалент с OR). Без GROUP BY, без ORDER BY.",
        exampleSql:
          "SELECT id, status FROM orders WHERE status IN ('pending', 'shipped');",
        checkSql:
          "SELECT id, status FROM orders WHERE status IN ('pending', 'shipped');",
      },
      {
        id: 'l04-t3',
        hint: 'Таблица products: электроника дешевле 2000 руб (в центах: 200000).',
        exampleSql:
          "SELECT name, price_cents FROM products WHERE category = 'Электроника' AND price_cents < 200000;",
        checkSql:
          "SELECT name, price_cents FROM products WHERE category = 'Электроника' AND price_cents < 200000;",
      },
      {
        id: 'l04-t4',
        hint: "Таблица customers. Вывести колонки: full_name, city. Фильтр WHERE: city IN ('Prague', 'Lisbon'). Без GROUP BY, без ORDER BY.",
        exampleSql:
          "SELECT full_name, city FROM customers WHERE city IN ('Prague', 'Lisbon');",
        checkSql:
          "SELECT full_name, city FROM customers WHERE city IN ('Prague', 'Lisbon');",
      },
    ],
  },
  {
    id: 'l05',
    title: 'ORDER BY и LIMIT',
    theory:
      'ORDER BY сортирует строки (ASC по умолчанию, DESC — по убыванию). LIMIT n ограничивает число строк. Сначала ORDER BY, потом LIMIT. Таблица в каждом задании названа явно. Для «топа» или «первых N» в условии всегда нужны и сортировка, и LIMIT — иначе СУБД вернёт произвольное подмножество строк.',
    tasks: [
      {
        id: 'l05-t1',
        hint: 'Таблица products: три самых дорогих товара по price_cents. Нужны ORDER BY price_cents DESC и LIMIT 3.',
        exampleSql: 'SELECT name, price_cents FROM products ORDER BY price_cents DESC LIMIT 3;',
        checkSql: 'SELECT name, price_cents FROM products ORDER BY price_cents DESC LIMIT 3;',
      },
      {
        id: 'l05-t2',
        hint: 'Таблица customers. Вывести колонку: full_name. Сортировка: ORDER BY full_name ASC (по алфавиту). Лимит: LIMIT 5. Без WHERE, без GROUP BY.',
        exampleSql: 'SELECT full_name FROM customers ORDER BY full_name LIMIT 5;',
        checkSql: 'SELECT full_name FROM customers ORDER BY full_name LIMIT 5;',
      },
      {
        id: 'l05-t3',
        hint: 'Таблица orders. Вывести колонки: id, order_date, total_cents. Сортировка: ORDER BY order_date DESC (сначала самые поздние даты). Лимит: LIMIT 3. Без WHERE, без GROUP BY.',
        exampleSql: 'SELECT id, order_date, total_cents FROM orders ORDER BY order_date DESC LIMIT 3;',
        checkSql: 'SELECT id, order_date, total_cents FROM orders ORDER BY order_date DESC LIMIT 3;',
      },
      {
        id: 'l05-t4',
        hint: 'Таблица order_items. Вывести колонки: id, order_id, line_total_cents. Сортировка: ORDER BY line_total_cents DESC. Лимит: LIMIT 2. Без WHERE, без GROUP BY.',
        exampleSql:
          'SELECT id, order_id, line_total_cents FROM order_items ORDER BY line_total_cents DESC LIMIT 2;',
        checkSql:
          'SELECT id, order_id, line_total_cents FROM order_items ORDER BY line_total_cents DESC LIMIT 2;',
      },
    ],
  },
  {
    id: 'l06',
    title: 'JOIN: заказы и покупатели',
    theory:
      'INNER JOIN связывает строки двух таблиц по условию в ON, например: FROM orders o JOIN customers c ON c.id = o.customer_id. Задания используют только orders и customers.',
    tasks: [
      {
        id: 'l06-t1',
        hint: 'Таблицы orders и customers. Вывести колонки: id заказа, order_date, full_name покупателя (например o.id, o.order_date, c.full_name). JOIN: customers.id = orders.customer_id. Все строки заказов. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT o.id, o.order_date, c.full_name
FROM orders o
JOIN customers c ON c.id = o.customer_id;`,
        checkSql: `SELECT o.id, o.order_date, c.full_name
FROM orders o
JOIN customers c ON c.id = o.customer_id;`,
      },
      {
        id: 'l06-t2',
        hint: 'Таблица orders. Вывести колонки: order_date, total_cents. Фильтр WHERE: customer_id = 1. Без JOIN (достаточно одной таблицы), без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT order_date, total_cents FROM orders WHERE customer_id = 1;`,
        checkSql: `SELECT order_date, total_cents FROM orders WHERE customer_id = 1;`,
      },
      {
        id: 'l06-t3',
        hint: 'Таблицы orders и customers. Вывести колонки: full_name покупателя, total_cents заказа. JOIN: customers.id = orders.customer_id. Фильтр WHERE: orders.id = 5. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT c.full_name, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.id = 5;`,
        checkSql: `SELECT c.full_name, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.id = 5;`,
      },
      {
        id: 'l06-t4',
        hint: "Таблица orders. Вывести одну строку: число заказов (COUNT(*), можно алиас cnt). Фильтр WHERE: status = 'paid'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT COUNT(*) AS cnt FROM orders WHERE status = 'paid';",
        checkSql: "SELECT COUNT(*) AS cnt FROM orders WHERE status = 'paid';",
      },
    ],
  },
  {
    id: 'l07',
    title: 'JOIN: позиции и товары',
    theory:
      'Связываем order_items с products по order_items.product_id = products.id (JOIN ... ON p.id = oi.product_id). Задание l07-t4 — только таблица order_items, без JOIN к products.',
    tasks: [
      {
        id: 'l07-t1',
        hint: 'Таблицы order_items и products. Вывести колонки: name товара, quantity (например p.name, oi.quantity). JOIN: products.id = order_items.product_id. Все строки order_items. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT p.name, oi.quantity
FROM order_items oi
JOIN products p ON p.id = oi.product_id;`,
        checkSql: `SELECT p.name, oi.quantity
FROM order_items oi
JOIN products p ON p.id = oi.product_id;`,
      },
      {
        id: 'l07-t2',
        hint: 'Таблицы order_items и products. Вывести колонки: sku, line_total_cents. JOIN: products.id = order_items.product_id. Фильтр WHERE: order_items.order_id = 3. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT p.sku, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 3;`,
        checkSql: `SELECT p.sku, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 3;`,
      },
      {
        id: 'l07-t3',
        hint: 'Таблицы order_items и products. Вывести колонки: category товара, line_total_cents позиции. JOIN: products.id = order_items.product_id. Фильтр WHERE: order_items.id = 7. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT p.category, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.id = 7;`,
        checkSql: `SELECT p.category, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.id = 7;`,
      },
      {
        id: 'l07-t4',
        hint: 'Таблица order_items. Вывести колонки: order_id, quantity. Фильтр WHERE: product_id = 2. Без JOIN, без GROUP BY, без ORDER BY.',
        exampleSql:
          'SELECT order_id, quantity FROM order_items WHERE product_id = 2;',
        checkSql: 'SELECT order_id, quantity FROM order_items WHERE product_id = 2;',
      },
    ],
  },
  {
    id: 'l08',
    title: 'Несколько таблиц',
    theory:
      'Цепочка JOIN: order_items → orders → customers и order_items → products. В заданиях перечислены нужные таблицы.',
    tasks: [
      {
        id: 'l08-t1',
        hint: 'Таблицы order_items, orders, customers, products. Вывести колонки: full_name покупателя, name товара. JOIN: order_items.order_id = orders.id, orders.customer_id = customers.id, order_items.product_id = products.id. Фильтр WHERE: order_items.order_id = 1. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT c.full_name, p.name
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 1;`,
        checkSql: `SELECT c.full_name, p.name
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 1;`,
      },
      {
        id: 'l08-t2',
        hint: 'Таблицы orders и customers. Вывести колонки: email покупателя, total_cents заказа. JOIN: customers.id = orders.customer_id. Фильтр WHERE: orders.id = 4. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT c.email, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.id = 4;`,
        checkSql: `SELECT c.email, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.id = 4;`,
      },
      {
        id: 'l08-t3',
        hint: 'Таблицы order_items, orders, products. Вывести колонки: order_date (из orders), sku (из products), quantity (из order_items). JOIN: order_items.order_id = orders.id, order_items.product_id = products.id. Все строки order_items. Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT o.order_date, p.sku, oi.quantity
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id;`,
        checkSql: `SELECT o.order_date, p.sku, oi.quantity
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id;`,
      },
      {
        id: 'l08-t4',
        hint: 'Таблицы order_items, orders, customers. Вывести колонки: city покупателя, status заказа. JOIN: order_items.order_id = orders.id, orders.customer_id = customers.id. Фильтр WHERE: order_items.id = 10. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT c.city, o.status
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
WHERE oi.id = 10;`,
        checkSql: `SELECT c.city, o.status
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
WHERE oi.id = 10;`,
      },
    ],
  },
  {
    id: 'l09',
    title: 'COUNT и GROUP BY',
    theory:
      'COUNT(*) считает строки в группе. GROUP BY задаёт поле группировки. Обычно в SELECT идут то же поле (или поля), по которым группируете, и COUNT(*) — вторую колонку удобно назвать алиасом (например cnt). Каждое задание указывает таблицу: products, orders, customers или order_items.',
    tasks: [
      {
        id: 'l09-t1',
        hint: 'Таблица products: сколько товаров в каждой category.',
        exampleSql: `SELECT category, COUNT(*) AS cnt FROM products GROUP BY category;`,
        checkSql: `SELECT category, COUNT(*) AS cnt FROM products GROUP BY category;`,
      },
      {
        id: 'l09-t2',
        hint: 'Таблица orders. Вывести колонки: status, COUNT(*) (алиас cnt). Группировка: GROUP BY status. Без WHERE, без HAVING, без ORDER BY.',
        exampleSql: `SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status;`,
        checkSql: `SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status;`,
      },
      {
        id: 'l09-t3',
        hint: 'Таблица customers. Вывести колонки: city, COUNT(*) (алиас cnt). Группировка: GROUP BY city. Без WHERE, без HAVING, без ORDER BY.',
        exampleSql: `SELECT city, COUNT(*) AS cnt FROM customers GROUP BY city;`,
        checkSql: `SELECT city, COUNT(*) AS cnt FROM customers GROUP BY city;`,
      },
      {
        id: 'l09-t4',
        hint: 'Таблица order_items. Вывести колонки: order_id, COUNT(*) (алиас cnt). Группировка: GROUP BY order_id. Без WHERE, без HAVING, без ORDER BY.',
        exampleSql: `SELECT order_id, COUNT(*) AS cnt FROM order_items GROUP BY order_id;`,
        checkSql: `SELECT order_id, COUNT(*) AS cnt FROM order_items GROUP BY order_id;`,
      },
    ],
  },
  {
    id: 'l10',
    title: 'HAVING',
    theory:
      'HAVING фильтрует группы после GROUP BY (в отличие от WHERE, который фильтрует строки до группировки). Задания используют customers, products или order_items.',
    tasks: [
      {
        id: 'l10-t1',
        hint: 'Таблица customers. Вывести колонки: city, COUNT(*) (алиас cnt). Группировка: GROUP BY city. Отбор групп: HAVING COUNT(*) > 1. Без ORDER BY.',
        exampleSql: `SELECT city, COUNT(*) AS cnt
FROM customers
GROUP BY city
HAVING COUNT(*) > 1;`,
        checkSql: `SELECT city, COUNT(*) AS cnt
FROM customers
GROUP BY city
HAVING COUNT(*) > 1;`,
      },
      {
        id: 'l10-t2',
        hint: 'Таблица products. Вывести колонки: category, COUNT(*) (алиас cnt). Группировка: GROUP BY category. Отбор групп: HAVING COUNT(*) > 2. Без ORDER BY.',
        exampleSql: `SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) > 2;`,
        checkSql: `SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) > 2;`,
      },
      {
        id: 'l10-t3',
        hint: 'Таблица order_items. Вывести колонки: order_id, COUNT(*) (алиас cnt). Группировка: GROUP BY order_id. Отбор групп: HAVING COUNT(*) > 1. Без ORDER BY.',
        exampleSql: `SELECT order_id, COUNT(*) AS cnt
FROM order_items
GROUP BY order_id
HAVING COUNT(*) > 1;`,
        checkSql: `SELECT order_id, COUNT(*) AS cnt
FROM order_items
GROUP BY order_id
HAVING COUNT(*) > 1;`,
      },
    ],
  },
  {
    id: 'l11',
    title: 'DISTINCT',
    theory:
      'DISTINCT убирает дубликаты строк в результате. В подсказках указано: customers, orders или products.',
    tasks: [
      {
        id: 'l11-t1',
        hint: 'Таблица customers. Вывести уникальные значения колонки city (SELECT DISTINCT city). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: 'SELECT DISTINCT city FROM customers;',
        checkSql: 'SELECT DISTINCT city FROM customers;',
      },
      {
        id: 'l11-t2',
        hint: 'Таблица orders: уникальные status; порядок строк не важен.',
        exampleSql: 'SELECT DISTINCT status FROM orders;',
        checkSql: 'SELECT DISTINCT status FROM orders;',
      },
      {
        id: 'l11-t3',
        hint: 'Таблица products. Вывести уникальные пары колонок category, name (SELECT DISTINCT) при фильтре WHERE price_cents > 50000. Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT DISTINCT category, name FROM products WHERE price_cents > 50000;`,
        checkSql: `SELECT DISTINCT category, name FROM products WHERE price_cents > 50000;`,
      },
    ],
  },
  {
    id: 'l12',
    title: 'LIKE',
    theory:
      'LIKE сопоставляет строки с шаблоном: % — любая последовательность символов, _ — один символ. Задания по таблицам products и customers.',
    tasks: [
      {
        id: 'l12-t1',
        hint: "Таблица products. Вывести колонку: name. Фильтр WHERE: name LIKE '%Bluetooth%'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT name FROM products WHERE name LIKE '%Bluetooth%';",
        checkSql: "SELECT name FROM products WHERE name LIKE '%Bluetooth%';",
      },
      {
        id: 'l12-t2',
        hint: "Таблица customers. Вывести колонку: email. Фильтр WHERE: email LIKE 'user1%'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT email FROM customers WHERE email LIKE 'user1%';",
        checkSql: "SELECT email FROM customers WHERE email LIKE 'user1%';",
      },
      {
        id: 'l12-t3',
        hint: "Таблица products. Вывести колонку: sku. Фильтр WHERE: sku LIKE '__U%' (третий символ U). Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT sku FROM products WHERE sku LIKE '__U%';",
        checkSql: "SELECT sku FROM products WHERE sku LIKE '__U%';",
      },
    ],
  },
  {
    id: 'l13',
    title: 'Даты и сравнения',
    theory:
      'Даты в формате ISO (YYYY-MM-DD) можно сравнивать как строки — лексикографический порядок совпадает с хронологическим. Для «в году» или «в месяце» допустимы сравнение >= / <= или шаблон LIKE (например дата начинается с 2024-). Задания: orders и customers.',
    tasks: [
      {
        id: 'l13-t1',
        hint: "Таблица orders. Вывести колонки: id, order_date. Фильтр WHERE: order_date >= '2025-06-01'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT id, order_date FROM orders WHERE order_date >= '2025-06-01';",
        checkSql: "SELECT id, order_date FROM orders WHERE order_date >= '2025-06-01';",
      },
      {
        id: 'l13-t2',
        hint: "Таблица customers. Вывести колонки: full_name, signup_date. Фильтр WHERE: signup_date LIKE '2024-%'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT full_name, signup_date FROM customers WHERE signup_date LIKE '2024-%';",
        checkSql: "SELECT full_name, signup_date FROM customers WHERE signup_date LIKE '2024-%';",
      },
      {
        id: 'l13-t3',
        hint: "Таблица orders. Вывести колонки: id, order_date, total_cents. Фильтр WHERE: order_date LIKE '2025-03-%'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT id, order_date, total_cents FROM orders WHERE order_date LIKE '2025-03-%';",
        checkSql: "SELECT id, order_date, total_cents FROM orders WHERE order_date LIKE '2025-03-%';",
      },
    ],
  },
  {
    id: 'l14',
    title: 'Подзапрос',
    theory:
      'Подзапрос в скобках возвращает набор значений или одно значение; часто используется с IN. Задания: products, orders + customers, order_items + products.',
    tasks: [
      {
        id: 'l14-t1',
        hint: 'Таблица products. Вывести колонки: name, price_cents. Фильтр WHERE: price_cents > (SELECT AVG(price_cents) FROM products). Без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT name, price_cents FROM products
WHERE price_cents > (SELECT AVG(price_cents) FROM products);`,
        checkSql: `SELECT name, price_cents FROM products
WHERE price_cents > (SELECT AVG(price_cents) FROM products);`,
      },
      {
        id: 'l14-t2',
        hint: "Таблица orders. Вывести колонки: id, order_date. Фильтр WHERE: customer_id IN (SELECT id FROM customers WHERE city = 'Berlin'). Без GROUP BY, без ORDER BY.",
        exampleSql: `SELECT id, order_date FROM orders
WHERE customer_id IN (SELECT id FROM customers WHERE city = 'Berlin');`,
        checkSql: `SELECT id, order_date FROM orders
WHERE customer_id IN (SELECT id FROM customers WHERE city = 'Berlin');`,
      },
      {
        id: 'l14-t3',
        hint: "Таблица order_items (без JOIN к products во внешнем запросе). Вывести колонки: id позиции, quantity. Фильтр WHERE: product_id IN (SELECT id FROM products WHERE category = 'Дом'). Без GROUP BY, без ORDER BY.",
        exampleSql: `SELECT oi.id, oi.quantity FROM order_items oi
WHERE oi.product_id IN (SELECT id FROM products WHERE category = 'Дом');`,
        checkSql: `SELECT oi.id, oi.quantity FROM order_items oi
WHERE oi.product_id IN (SELECT id FROM products WHERE category = 'Дом');`,
      },
    ],
  },
  {
    id: 'l15',
    title: 'Агрегаты и JOIN',
    theory:
      'Суммы и средние по группам: SUM, AVG, JOIN orders с customers или order_items с products, затем GROUP BY. Для «топа по сумме» после группировки нужны ORDER BY по агрегату и LIMIT. В подсказках перечислены таблицы.',
    tasks: [
      {
        id: 'l15-t1',
        hint: 'Таблица order_items. Вывести колонки: order_id, SUM(line_total_cents) (алиас sum_lines). Группировка: GROUP BY order_id. Без WHERE, без HAVING, без ORDER BY.',
        exampleSql: `SELECT order_id, SUM(line_total_cents) AS sum_lines
FROM order_items
GROUP BY order_id;`,
        checkSql: `SELECT order_id, SUM(line_total_cents) AS sum_lines
FROM order_items
GROUP BY order_id;`,
      },
      {
        id: 'l15-t2',
        hint: 'Таблицы orders и customers. Вывести колонки: full_name, сумма total_cents по заказам (SUM, алиас spent). JOIN: customers.id = orders.customer_id. Группировка: GROUP BY customers.id, full_name. Сортировка: ORDER BY spent DESC. Лимит: LIMIT 8.',
        exampleSql: `SELECT c.full_name, SUM(o.total_cents) AS spent
FROM orders o
JOIN customers c ON c.id = o.customer_id
GROUP BY c.id, c.full_name
ORDER BY spent DESC
LIMIT 8;`,
        checkSql: `SELECT c.full_name, SUM(o.total_cents) AS spent
FROM orders o
JOIN customers c ON c.id = o.customer_id
GROUP BY c.id, c.full_name
ORDER BY spent DESC
LIMIT 8;`,
      },
      {
        id: 'l15-t3',
        hint: 'Таблицы order_items и products. Вывести колонки: category, SUM(quantity) (алиас units). JOIN: products.id = order_items.product_id. Группировка: GROUP BY p.category. Без WHERE, без HAVING, без ORDER BY.',
        exampleSql: `SELECT p.category, SUM(oi.quantity) AS units
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.category;`,
        checkSql: `SELECT p.category, SUM(oi.quantity) AS units
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.category;`,
      },
      {
        id: 'l15-t4',
        hint: "Таблица orders. Вывести одну строку: AVG(total_cents) (алиас avg_total). Фильтр WHERE: status = 'paid'. Без GROUP BY, без ORDER BY.",
        exampleSql: "SELECT AVG(total_cents) AS avg_total FROM orders WHERE status = 'paid';",
        checkSql: "SELECT AVG(total_cents) AS avg_total FROM orders WHERE status = 'paid';",
      },
    ],
  },
  {
    id: 'l16',
    title: 'Итог: магазин в одном запросе',
    theory:
      'Итоговые отчёты: customers + orders, order_items + products, агрегаты по order_items. Таблицы указаны в каждой подсказке.',
    tasks: [
      {
        id: 'l16-t1',
        hint: "Таблицы orders и customers. Вывести колонки: full_name, order_date, total_cents. JOIN: customers.id = orders.customer_id. Фильтр WHERE: orders.status = 'shipped'. Без GROUP BY, без ORDER BY.",
        exampleSql: `SELECT c.full_name, o.order_date, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'shipped';`,
        checkSql: `SELECT c.full_name, o.order_date, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'shipped';`,
      },
      {
        id: 'l16-t2',
        hint: 'Таблицы order_items и products. Вывести колонки: name товара, SUM(line_total_cents) (алиас revenue). JOIN: products.id = order_items.product_id. Группировка: GROUP BY id товара и name (как в эталоне: p.id, p.name). Сортировка: ORDER BY revenue DESC. Лимит: LIMIT 5.',
        exampleSql: `SELECT p.name, SUM(oi.line_total_cents) AS revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 5;`,
        checkSql: `SELECT p.name, SUM(oi.line_total_cents) AS revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 5;`,
      },
      {
        id: 'l16-t3',
        hint: 'Таблицы customers и orders. Вывести колонки: full_name, COUNT(o.id) (алиас order_cnt). JOIN: orders.customer_id = customers.id. Группировка: GROUP BY customers.id, full_name. Отбор групп: HAVING COUNT(o.id) > 1. Без ORDER BY.',
        exampleSql: `SELECT c.full_name, COUNT(o.id) AS order_cnt
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.full_name
HAVING COUNT(o.id) > 1;`,
        checkSql: `SELECT c.full_name, COUNT(o.id) AS order_cnt
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.full_name
HAVING COUNT(o.id) > 1;`,
      },
      {
        id: 'l16-t4',
        hint: 'Таблица order_items. Вывести одну строку с двумя числами: COUNT(*) и COUNT(DISTINCT product_id) (алиасы positions и unique_products по желанию). Без WHERE, без GROUP BY, без ORDER BY.',
        exampleSql: `SELECT COUNT(*) AS positions, COUNT(DISTINCT product_id) AS unique_products FROM order_items;`,
        checkSql: `SELECT COUNT(*) AS positions, COUNT(DISTINCT product_id) AS unique_products FROM order_items;`,
      },
    ],
  },
];

export const DEFAULT_EDITOR_SQL = 'SELECT * FROM customers LIMIT 5;';

export const SQL_PROGRESS_STORAGE_KEY = 'qa-sql-progress-v1';

/** Плоский список всех task id для восстановления прогресса */
export function allTaskIds() {
  const ids = [];
  for (const lesson of SQL_LESSONS) {
    for (const t of lesson.tasks) {
      ids.push(t.id);
    }
  }
  return ids;
}

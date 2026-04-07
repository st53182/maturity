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
    order.map((o) => (row[o.i] == null ? '' : String(row[o.i]))).join('\u001f'),
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

  const ok = gridsMatch(
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

/** Урок с подзаданиями; check.sql — эталонный SELECT (детерминированный ORDER BY). */
export const SQL_LESSONS = [
  {
    id: 'l01',
    title: 'Таблицы и первый SELECT',
    theory:
      'Данные интернет-магазина: покупатели (customers), товары (products), заказы (orders) и позиции заказа (order_items). SELECT читает строки; * — все колонки. Запросы выполняются только в браузере.',
    tasks: [
      {
        id: 'l01-t1',
        hint: 'Покажите все колонки всех покупателей.',
        exampleSql: 'SELECT * FROM customers;',
        checkSql: 'SELECT * FROM customers ORDER BY id;',
      },
      {
        id: 'l01-t2',
        hint: 'Покажите все колонки всех товаров.',
        exampleSql: 'SELECT * FROM products;',
        checkSql: 'SELECT * FROM products ORDER BY id;',
      },
      {
        id: 'l01-t3',
        hint: 'Покажите все колонки заказов (таблица orders).',
        exampleSql: 'SELECT * FROM orders;',
        checkSql: 'SELECT * FROM orders ORDER BY id;',
      },
      {
        id: 'l01-t4',
        hint: 'Покажите все позиции заказов из order_items.',
        exampleSql: 'SELECT * FROM order_items;',
        checkSql: 'SELECT * FROM order_items ORDER BY id;',
      },
    ],
  },
  {
    id: 'l02',
    title: 'Выбор колонок',
    theory:
      'Вместо * перечисляют нужные поля через запятую — меньше шума и проще читать результат.',
    tasks: [
      {
        id: 'l02-t1',
        hint: 'Выведите только имя, email и город покупателей.',
        exampleSql: 'SELECT full_name, email, city FROM customers;',
        checkSql: 'SELECT full_name, email, city FROM customers ORDER BY full_name;',
      },
      {
        id: 'l02-t2',
        hint: 'Для товаров выведите sku, название и цену в центах (price_cents).',
        exampleSql: 'SELECT sku, name, price_cents FROM products;',
        checkSql: 'SELECT sku, name, price_cents FROM products ORDER BY sku;',
      },
      {
        id: 'l02-t3',
        hint: 'Для заказов: id, дата заказа и статус.',
        exampleSql: 'SELECT id, order_date, status FROM orders;',
        checkSql: 'SELECT id, order_date, status FROM orders ORDER BY id;',
      },
      {
        id: 'l02-t4',
        hint: 'Для позиций заказа: id заказа, id товара и количество.',
        exampleSql: 'SELECT order_id, product_id, quantity FROM order_items;',
        checkSql: 'SELECT order_id, product_id, quantity FROM order_items ORDER BY id;',
      },
    ],
  },
  {
    id: 'l03',
    title: 'WHERE: фильтр строк',
    theory:
      'WHERE оставляет только строки, для которых условие истинно. Строки в кавычках, числа — без кавычек.',
    tasks: [
      {
        id: 'l03-t1',
        hint: 'Товары категории «Электроника».',
        exampleSql: "SELECT * FROM products WHERE category = 'Электроника';",
        checkSql:
          "SELECT * FROM products WHERE category = 'Электроника' ORDER BY id;",
      },
      {
        id: 'l03-t2',
        hint: 'Заказы со статусом paid.',
        exampleSql: "SELECT * FROM orders WHERE status = 'paid';",
        checkSql: "SELECT * FROM orders WHERE status = 'paid' ORDER BY id;",
      },
      {
        id: 'l03-t3',
        hint: 'Покупатели из Берлина (в таблице city хранится как Berlin).',
        exampleSql: "SELECT full_name, email FROM customers WHERE city = 'Berlin';",
        checkSql:
          "SELECT full_name, email FROM customers WHERE city = 'Berlin' ORDER BY full_name;",
      },
      {
        id: 'l03-t4',
        hint: 'Позиции заказа с количеством не меньше 3.',
        exampleSql: 'SELECT * FROM order_items WHERE quantity >= 3;',
        checkSql: 'SELECT * FROM order_items WHERE quantity >= 3 ORDER BY id;',
      },
    ],
  },
  {
    id: 'l04',
    title: 'AND, OR и IN',
    theory:
      'AND и OR объединяют условия. IN (список) удобен, когда поле должно быть одним из нескольких значений.',
    tasks: [
      {
        id: 'l04-t1',
        hint: 'Товары категории «Книги» или «Спорт».',
        exampleSql:
          "SELECT name, category FROM products WHERE category IN ('Книги', 'Спорт');",
        checkSql:
          "SELECT name, category FROM products WHERE category IN ('Книги', 'Спорт') ORDER BY category, name;",
      },
      {
        id: 'l04-t2',
        hint: 'Заказы со статусом pending или shipped.',
        exampleSql:
          "SELECT id, status FROM orders WHERE status = 'pending' OR status = 'shipped';",
        checkSql:
          "SELECT id, status FROM orders WHERE status IN ('pending', 'shipped') ORDER BY id;",
      },
      {
        id: 'l04-t3',
        hint: 'Электроника дешевле 2000 руб (в центах: 200000).',
        exampleSql:
          "SELECT name, price_cents FROM products WHERE category = 'Электроника' AND price_cents < 200000;",
        checkSql:
          "SELECT name, price_cents FROM products WHERE category = 'Электроника' AND price_cents < 200000 ORDER BY price_cents;",
      },
      {
        id: 'l04-t4',
        hint: 'Покупатели из Праги или Лиссабона (Prague, Lisbon).',
        exampleSql:
          "SELECT full_name, city FROM customers WHERE city = 'Prague' OR city = 'Lisbon';",
        checkSql:
          "SELECT full_name, city FROM customers WHERE city IN ('Prague', 'Lisbon') ORDER BY city, full_name;",
      },
    ],
  },
  {
    id: 'l05',
    title: 'ORDER BY и LIMIT',
    theory:
      'ORDER BY сортирует строки (ASC по умолчанию, DESC — по убыванию). LIMIT n ограничивает число строк. Сначала ORDER BY, потом LIMIT.',
    tasks: [
      {
        id: 'l05-t1',
        hint: 'Три самых дорогих товара по price_cents (сначала дороже).',
        exampleSql: 'SELECT name, price_cents FROM products ORDER BY price_cents DESC LIMIT 3;',
        checkSql: 'SELECT name, price_cents FROM products ORDER BY price_cents DESC LIMIT 3;',
      },
      {
        id: 'l05-t2',
        hint: 'Пять первых покупателей по алфавиту имён.',
        exampleSql: 'SELECT full_name FROM customers ORDER BY full_name LIMIT 5;',
        checkSql: 'SELECT full_name FROM customers ORDER BY full_name LIMIT 5;',
      },
      {
        id: 'l05-t3',
        hint: 'Три последних заказа по дате (order_date по убыванию).',
        exampleSql: 'SELECT id, order_date, total_cents FROM orders ORDER BY order_date DESC LIMIT 3;',
        checkSql: 'SELECT id, order_date, total_cents FROM orders ORDER BY order_date DESC LIMIT 3;',
      },
      {
        id: 'l05-t4',
        hint: 'Две позиции с наибольшим line_total_cents.',
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
      'INNER JOIN связывает строки двух таблиц по условию. Здесь orders.customer_id = customers.id.',
    tasks: [
      {
        id: 'l06-t1',
        hint: 'Для каждого заказа покажите id заказа, дату и имя покупателя.',
        exampleSql: `SELECT o.id, o.order_date, c.full_name
FROM orders o
JOIN customers c ON c.id = o.customer_id
ORDER BY o.id
LIMIT 8;`,
        checkSql: `SELECT o.id, o.order_date, c.full_name
FROM orders o
JOIN customers c ON c.id = o.customer_id
ORDER BY o.id
LIMIT 8;`,
      },
      {
        id: 'l06-t2',
        hint: 'Заказы покупателя с id = 1: дата и total_cents.',
        exampleSql: `SELECT order_date, total_cents FROM orders WHERE customer_id = 1 ORDER BY order_date;`,
        checkSql: `SELECT order_date, total_cents FROM orders WHERE customer_id = 1 ORDER BY order_date;`,
      },
      {
        id: 'l06-t3',
        hint: 'Имя покупателя и сумма заказа для заказа id = 5.',
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
        hint: 'Сколько заказов у каждого статуса (одной строкой: paid).',
        exampleSql: "SELECT COUNT(*) AS cnt FROM orders WHERE status = 'paid';",
        checkSql: "SELECT COUNT(*) AS cnt FROM orders WHERE status = 'paid';",
      },
    ],
  },
  {
    id: 'l07',
    title: 'JOIN: позиции и товары',
    theory:
      'Связываем order_items с products по product_id, чтобы видеть название товара в строке заказа.',
    tasks: [
      {
        id: 'l07-t1',
        hint: 'Название товара и quantity для каждой позиции (первые 10 по id позиции).',
        exampleSql: `SELECT p.name, oi.quantity
FROM order_items oi
JOIN products p ON p.id = oi.product_id
ORDER BY oi.id
LIMIT 10;`,
        checkSql: `SELECT p.name, oi.quantity
FROM order_items oi
JOIN products p ON p.id = oi.product_id
ORDER BY oi.id
LIMIT 10;`,
      },
      {
        id: 'l07-t2',
        hint: 'sku и line_total_cents для позиций заказа order_id = 3.',
        exampleSql: `SELECT p.sku, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 3
ORDER BY oi.id;`,
        checkSql: `SELECT p.sku, oi.line_total_cents
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 3
ORDER BY oi.id;`,
      },
      {
        id: 'l07-t3',
        hint: 'Категория и сумма строки для позиции id = 7.',
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
        hint: 'Все позиции товара с id = 2: order_id и quantity.',
        exampleSql:
          'SELECT order_id, quantity FROM order_items WHERE product_id = 2 ORDER BY id;',
        checkSql: 'SELECT order_id, quantity FROM order_items WHERE product_id = 2 ORDER BY id;',
      },
    ],
  },
  {
    id: 'l08',
    title: 'Несколько таблиц',
    theory:
      'Цепочка JOIN: заказ → покупатель, позиция → товар. Условия связывания перечисляют через JOIN.',
    tasks: [
      {
        id: 'l08-t1',
        hint: 'Имя покупателя и название товара для позиций с order_id = 1.',
        exampleSql: `SELECT c.full_name, p.name
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 1
ORDER BY p.name;`,
        checkSql: `SELECT c.full_name, p.name
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN customers c ON c.id = o.customer_id
JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = 1
ORDER BY p.name;`,
      },
      {
        id: 'l08-t2',
        hint: 'Для заказа id = 4: email покупателя и total_cents заказа.',
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
        hint: 'Дата заказа, sku и quantity (первые 6 строк по id позиции).',
        exampleSql: `SELECT o.order_date, p.sku, oi.quantity
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
ORDER BY oi.id
LIMIT 6;`,
        checkSql: `SELECT o.order_date, p.sku, oi.quantity
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
ORDER BY oi.id
LIMIT 6;`,
      },
      {
        id: 'l08-t4',
        hint: 'Город покупателя и статус заказа для позиции order_items.id = 10.',
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
      'COUNT(*) считает строки в группе. GROUP BY задаёт, по какому полю группировать (например категория товара).',
    tasks: [
      {
        id: 'l09-t1',
        hint: 'Сколько товаров в каждой категории.',
        exampleSql: `SELECT category, COUNT(*) AS cnt FROM products GROUP BY category ORDER BY category;`,
        checkSql: `SELECT category, COUNT(*) AS cnt FROM products GROUP BY category ORDER BY category;`,
      },
      {
        id: 'l09-t2',
        hint: 'Сколько заказов у каждого статуса.',
        exampleSql: `SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status ORDER BY status;`,
        checkSql: `SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status ORDER BY status;`,
      },
      {
        id: 'l09-t3',
        hint: 'Сколько покупателей в каждом городе.',
        exampleSql: `SELECT city, COUNT(*) AS cnt FROM customers GROUP BY city ORDER BY city;`,
        checkSql: `SELECT city, COUNT(*) AS cnt FROM customers GROUP BY city ORDER BY city;`,
      },
      {
        id: 'l09-t4',
        hint: 'Сколько позиций приходится на каждый order_id (первые 8 по order_id).',
        exampleSql: `SELECT order_id, COUNT(*) AS cnt FROM order_items GROUP BY order_id ORDER BY order_id LIMIT 8;`,
        checkSql: `SELECT order_id, COUNT(*) AS cnt FROM order_items GROUP BY order_id ORDER BY order_id LIMIT 8;`,
      },
    ],
  },
  {
    id: 'l10',
    title: 'HAVING',
    theory:
      'HAVING фильтрует группы после GROUP BY (в отличие от WHERE, который фильтрует строки до группировки).',
    tasks: [
      {
        id: 'l10-t1',
        hint: 'Города, где больше одного покупателя.',
        exampleSql: `SELECT city, COUNT(*) AS cnt
FROM customers
GROUP BY city
HAVING COUNT(*) > 1
ORDER BY city;`,
        checkSql: `SELECT city, COUNT(*) AS cnt
FROM customers
GROUP BY city
HAVING COUNT(*) > 1
ORDER BY city;`,
      },
      {
        id: 'l10-t2',
        hint: 'Товарные категории с более чем двумя товарами.',
        exampleSql: `SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) > 2
ORDER BY category;`,
        checkSql: `SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) > 2
ORDER BY category;`,
      },
      {
        id: 'l10-t3',
        hint: 'order_id, по которым больше одной позиции (первые 10 по order_id).',
        exampleSql: `SELECT order_id, COUNT(*) AS cnt
FROM order_items
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY order_id
LIMIT 10;`,
        checkSql: `SELECT order_id, COUNT(*) AS cnt
FROM order_items
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY order_id
LIMIT 10;`,
      },
    ],
  },
  {
    id: 'l11',
    title: 'DISTINCT',
    theory:
      'DISTINCT убирает дубликаты строк в результате — полезно для списка уникальных значений.',
    tasks: [
      {
        id: 'l11-t1',
        hint: 'Уникальные города покупателей (отсортированы).',
        exampleSql: 'SELECT DISTINCT city FROM customers ORDER BY city;',
        checkSql: 'SELECT DISTINCT city FROM customers ORDER BY city;',
      },
      {
        id: 'l11-t2',
        hint: 'Уникальные статусы заказов.',
        exampleSql: 'SELECT DISTINCT status FROM orders ORDER BY status;',
        checkSql: 'SELECT DISTINCT status FROM orders ORDER BY status;',
      },
      {
        id: 'l11-t3',
        hint: 'Уникальные пары (category, name) для товаров дороже 50000 центов.',
        exampleSql: `SELECT DISTINCT category, name FROM products WHERE price_cents > 50000 ORDER BY category, name;`,
        checkSql: `SELECT DISTINCT category, name FROM products WHERE price_cents > 50000 ORDER BY category, name;`,
      },
    ],
  },
  {
    id: 'l12',
    title: 'LIKE',
    theory:
      'LIKE сопоставляет строки с шаблоном: % — любая последовательность символов, _ — один символ.',
    tasks: [
      {
        id: 'l12-t1',
        hint: 'Товары, в названии которых есть подстрока «Bluetooth» (латиница, удобно для LIKE).',
        exampleSql: "SELECT name FROM products WHERE name LIKE '%Bluetooth%';",
        checkSql: "SELECT name FROM products WHERE name LIKE '%Bluetooth%' ORDER BY name;",
      },
      {
        id: 'l12-t2',
        hint: 'Email покупателей, начинающихся на «user1».',
        exampleSql: "SELECT email FROM customers WHERE email LIKE 'user1%';",
        checkSql: "SELECT email FROM customers WHERE email LIKE 'user1%' ORDER BY email;",
      },
      {
        id: 'l12-t3',
        hint: 'SKU, третий символ которого «U» (шаблон _ _ U%).',
        exampleSql: "SELECT sku FROM products WHERE sku LIKE '__U%';",
        checkSql: "SELECT sku FROM products WHERE sku LIKE '__U%' ORDER BY sku;",
      },
    ],
  },
  {
    id: 'l13',
    title: 'Даты и сравнения',
    theory:
      'Даты в формате ISO (YYYY-MM-DD) можно сравнивать как строки — лексикографический порядок совпадает с хронологическим.',
    tasks: [
      {
        id: 'l13-t1',
        hint: 'Заказы с датой не раньше 2025-06-01.',
        exampleSql: "SELECT id, order_date FROM orders WHERE order_date >= '2025-06-01' ORDER BY order_date;",
        checkSql: "SELECT id, order_date FROM orders WHERE order_date >= '2025-06-01' ORDER BY order_date;",
      },
      {
        id: 'l13-t2',
        hint: 'Покупатели, зарегистрированные в 2024 году (signup_date начинается с 2024-).',
        exampleSql: "SELECT full_name, signup_date FROM customers WHERE signup_date LIKE '2024-%' ORDER BY signup_date;",
        checkSql: "SELECT full_name, signup_date FROM customers WHERE signup_date LIKE '2024-%' ORDER BY signup_date;",
      },
      {
        id: 'l13-t3',
        hint: 'Заказы в марте 2025 (дата вида 2025-03-%).',
        exampleSql: "SELECT id, order_date, total_cents FROM orders WHERE order_date LIKE '2025-03-%' ORDER BY order_date;",
        checkSql: "SELECT id, order_date, total_cents FROM orders WHERE order_date LIKE '2025-03-%' ORDER BY order_date;",
      },
    ],
  },
  {
    id: 'l14',
    title: 'Подзапрос',
    theory:
      'Подзапрос в скобках возвращает набор значений или одно значение; часто используется с IN.',
    tasks: [
      {
        id: 'l14-t1',
        hint: 'Товары, цена которых выше средней price_cents по всем товарам.',
        exampleSql: `SELECT name, price_cents FROM products
WHERE price_cents > (SELECT AVG(price_cents) FROM products)
ORDER BY price_cents;`,
        checkSql: `SELECT name, price_cents FROM products
WHERE price_cents > (SELECT AVG(price_cents) FROM products)
ORDER BY price_cents;`,
      },
      {
        id: 'l14-t2',
        hint: 'Заказы покупателей из Берлина (customer_id IN подзапросом по city = Berlin).',
        exampleSql: `SELECT id, order_date FROM orders
WHERE customer_id IN (SELECT id FROM customers WHERE city = 'Berlin')
ORDER BY order_date;`,
        checkSql: `SELECT id, order_date FROM orders
WHERE customer_id IN (SELECT id FROM customers WHERE city = 'Berlin')
ORDER BY order_date;`,
      },
      {
        id: 'l14-t3',
        hint: 'Позиции заказов для товаров категории «Дом» (product_id IN ...).',
        exampleSql: `SELECT oi.id, oi.quantity FROM order_items oi
WHERE oi.product_id IN (SELECT id FROM products WHERE category = 'Дом')
ORDER BY oi.id
LIMIT 12;`,
        checkSql: `SELECT oi.id, oi.quantity FROM order_items oi
WHERE oi.product_id IN (SELECT id FROM products WHERE category = 'Дом')
ORDER BY oi.id
LIMIT 12;`,
      },
    ],
  },
  {
    id: 'l15',
    title: 'Агрегаты и JOIN',
    theory:
      'Можно считать суммы по группам после соединения таблиц — важно не смешивать уровень строк и групп без GROUP BY.',
    tasks: [
      {
        id: 'l15-t1',
        hint: 'Сумма line_total_cents по каждому order_id (первые 10 заказов по id).',
        exampleSql: `SELECT order_id, SUM(line_total_cents) AS sum_lines
FROM order_items
GROUP BY order_id
ORDER BY order_id
LIMIT 10;`,
        checkSql: `SELECT order_id, SUM(line_total_cents) AS sum_lines
FROM order_items
GROUP BY order_id
ORDER BY order_id
LIMIT 10;`,
      },
      {
        id: 'l15-t2',
        hint: 'Имя покупателя и сумма всех его заказов (total_cents) — группировка по customer_id из orders с JOIN.',
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
        hint: 'Категория и суммарное количество проданных единиц (SUM quantity по order_items + products).',
        exampleSql: `SELECT p.category, SUM(oi.quantity) AS units
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.category
ORDER BY p.category;`,
        checkSql: `SELECT p.category, SUM(oi.quantity) AS units
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.category
ORDER BY p.category;`,
      },
      {
        id: 'l15-t4',
        hint: 'Средняя total_cents по заказам со статусом paid.',
        exampleSql: "SELECT AVG(total_cents) AS avg_total FROM orders WHERE status = 'paid';",
        checkSql: "SELECT AVG(total_cents) AS avg_total FROM orders WHERE status = 'paid';",
      },
    ],
  },
  {
    id: 'l16',
    title: 'Итог: магазин в одном запросе',
    theory:
      'Соберите JOIN, фильтр и сортировку: типичный отчёт «кто что купил».',
    tasks: [
      {
        id: 'l16-t1',
        hint: 'Для заказов со статусом shipped: имя покупателя, дата заказа, total_cents.',
        exampleSql: `SELECT c.full_name, o.order_date, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'shipped'
ORDER BY o.order_date;`,
        checkSql: `SELECT c.full_name, o.order_date, o.total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'shipped'
ORDER BY o.order_date;`,
      },
      {
        id: 'l16-t2',
        hint: 'Топ-5 товаров по выручке (SUM line_total_cents), с названием товара.',
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
        hint: 'Покупатели с более чем одним заказом: имя и число заказов.',
        exampleSql: `SELECT c.full_name, COUNT(o.id) AS order_cnt
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.full_name
HAVING COUNT(o.id) > 1
ORDER BY order_cnt DESC;`,
        checkSql: `SELECT c.full_name, COUNT(o.id) AS order_cnt
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.full_name
HAVING COUNT(o.id) > 1
ORDER BY order_cnt DESC;`,
      },
      {
        id: 'l16-t4',
        hint: 'Одна строка: сколько всего позиций в заказах и сколько уникальных товаров в этих позициях.',
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

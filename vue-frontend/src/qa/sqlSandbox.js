/**
 * Демо-данные и уроки для QA SQL-тренажёра (SQLite через sql.js, только в браузере).
 */

function esc(s) {
  return String(s).replace(/'/g, "''");
}

const SEVERITIES = ['Critical', 'Major', 'Minor', 'Trivial'];
const STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed'];
const ASSIGNEES = ['Иван П.', 'Мария К.', 'Алексей В.', 'Ольга С.', 'Дмитрий Н.'];
const SPRINTS = ['2025.1', '2025.2', '2025.3', 'Backlog'];
const SUMMARIES = [
  'Падение при сохранении формы',
  'Неверный расчёт итога в корзине',
  'Ошибка валидации email',
  'Таймаут при вызове API отчёта',
  'Некорректная строка в локализации',
  'Обрезание длинного комментария',
  'Дубликат записи при повторном клике',
  'Потеря черновика при смене вкладки',
];

const BUILDS = ['1.2.0', '1.2.1', '1.3.0-beta', '1.3.0-rc1'];
const RESULTS = ['Passed', 'Failed', 'Blocked', 'Skipped'];
const ENVS = ['staging', 'preprod', 'test'];

function buildDefectRows(count = 24) {
  const rows = [];
  for (let i = 1; i <= count; i++) {
    rows.push({
      id: i,
      defect_key: `GB-${2000 + i}`,
      summary: `${SUMMARIES[i % SUMMARIES.length]} (#${i})`,
      severity: SEVERITIES[i % SEVERITIES.length],
      status: STATUSES[i % STATUSES.length],
      assignee: ASSIGNEES[i % ASSIGNEES.length],
      created_at: `2025-${String((i % 12) + 1).padStart(2, '0')}-${String((i % 28) + 1).padStart(2, '0')}`,
      sprint: SPRINTS[i % SPRINTS.length],
    });
  }
  return rows;
}

function buildTestRunRows(count = 24) {
  const rows = [];
  for (let i = 1; i <= count; i++) {
    const defectId = ((i - 1) % 24) + 1;
    rows.push({
      id: i,
      defect_id: defectId,
      build_number: BUILDS[i % BUILDS.length],
      result: RESULTS[i % RESULTS.length],
      executor: ASSIGNEES[(i + 2) % ASSIGNEES.length],
      duration_minutes: (i % 120) + 5,
      environment: ENVS[i % ENVS.length],
      run_date: `2025-03-${String((i % 28) + 1).padStart(2, '0')}`,
    });
  }
  return rows;
}

/**
 * SQL для создания и заполнения таблиц defects (8 колонок) и test_runs (8 колонок), по 24 строки.
 */
export function getSeedSQL() {
  const defects = buildDefectRows(24);
  const runs = buildTestRunRows(24);

  const dCols =
    '(id, defect_key, summary, severity, status, assignee, created_at, sprint)';
  const dVals = defects
    .map(
      (r) =>
        `(${r.id}, '${esc(r.defect_key)}', '${esc(r.summary)}', '${esc(r.severity)}', '${esc(r.status)}', '${esc(r.assignee)}', '${esc(r.created_at)}', '${esc(r.sprint)}')`,
    )
    .join(',\n');

  const rCols =
    '(id, defect_id, build_number, result, executor, duration_minutes, environment, run_date)';
  const rVals = runs
    .map(
      (r) =>
        `(${r.id}, ${r.defect_id}, '${esc(r.build_number)}', '${esc(r.result)}', '${esc(r.executor)}', ${r.duration_minutes}, '${esc(r.environment)}', '${esc(r.run_date)}')`,
    )
    .join(',\n');

  return `
DROP TABLE IF EXISTS test_runs;
DROP TABLE IF EXISTS defects;

CREATE TABLE defects (
  id INTEGER PRIMARY KEY,
  defect_key TEXT NOT NULL,
  summary TEXT,
  severity TEXT,
  status TEXT,
  assignee TEXT,
  created_at TEXT,
  sprint TEXT
);

CREATE TABLE test_runs (
  id INTEGER PRIMARY KEY,
  defect_id INTEGER NOT NULL,
  build_number TEXT,
  result TEXT,
  executor TEXT,
  duration_minutes INTEGER,
  environment TEXT,
  run_date TEXT,
  FOREIGN KEY (defect_id) REFERENCES defects(id)
);

INSERT INTO defects ${dCols} VALUES
${dVals};

INSERT INTO test_runs ${rCols} VALUES
${rVals};
`.trim();
}

/** Уроки: собственные формулировки на русском, порядок тем как в классическом вводном курсе SQL */
export const SQL_LESSONS = [
  {
    id: 'intro',
    title: 'Введение: таблицы и SQL',
    theory:
      'Реляционная база хранит данные в таблицах: строки — записи, столбцы — атрибуты (поля). Язык SQL описывает, какие данные получить или как их изменить. Здесь две таблицы: defects (дефекты) и test_runs (прогоны тестов), связанные полем defect_id. Запросы выполняются только в вашем браузере; на сервер ничего не отправляется.',
    hint: 'Попробуйте вывести все колонки всех дефектов.',
    exampleSql: 'SELECT * FROM defects;',
  },
  {
    id: 'select-cols',
    title: 'SELECT: выбор колонок',
    theory:
      'Звёздочка * означает «все колонки». Можно перечислить нужные поля через запятую — так результат компактнее и понятнее.',
    hint: 'Выведите только ключ, краткое описание и серьёзность дефекта.',
    exampleSql: 'SELECT defect_key, summary, severity FROM defects;',
  },
  {
    id: 'where',
    title: 'WHERE: фильтрация строк',
    theory:
      'Условие WHERE оставляет только строки, для которых выражение истинно. Часто сравнивают колонку с текстом или числом в кавычках для строк.',
    hint: 'Покажите дефекты со статусом Open.',
    exampleSql: "SELECT * FROM defects WHERE status = 'Open';",
  },
  {
    id: 'where-advanced',
    title: 'AND, OR и IN',
    theory:
      'Несколько условий объединяют AND (оба верны) и OR (хотя бы одно). Оператор IN (...) удобен, когда значение должно входить в список.',
    hint: 'Дефекты с серьёзностью Critical или Major.',
    exampleSql:
      "SELECT defect_key, summary, severity FROM defects WHERE severity IN ('Critical', 'Major');",
  },
  {
    id: 'order-limit',
    title: 'ORDER BY и LIMIT',
    theory:
      'ORDER BY сортирует результат (по умолчанию по возрастанию; DESC — по убыванию). LIMIT n ограничивает число строк — полезно для «топа».',
    hint: 'Пять самых «свежих» по дате создания дефектов (по убыванию даты).',
    exampleSql: 'SELECT defect_key, created_at FROM defects ORDER BY created_at DESC LIMIT 5;',
  },
  {
    id: 'join',
    title: 'JOIN двух таблиц',
    theory:
      'JOIN соединяет строки из двух таблиц по условию. Чаще всего — INNER JOIN: остаются пары, где условие истинно. Здесь test_runs.defect_id ссылается на defects.id.',
    hint: 'Покажите ключ дефекта, результат прогона и сборку.',
    exampleSql: `SELECT d.defect_key, t.result, t.build_number
FROM defects d
JOIN test_runs t ON t.defect_id = d.id
LIMIT 10;`,
  },
  {
    id: 'aggregate',
    title: 'COUNT и GROUP BY',
    theory:
      'COUNT(*) считает строки в группе. GROUP BY задаёт группы (например, по статусу или исполнителю). Так получают сводки по данным.',
    hint: 'Сколько прогонов по каждому результату (Passed, Failed, …).',
    exampleSql: `SELECT result, COUNT(*) AS cnt
FROM test_runs
GROUP BY result
ORDER BY cnt DESC;`,
  },
];

export const DEFAULT_EDITOR_SQL = "SELECT * FROM defects LIMIT 10;";

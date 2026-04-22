# GrowBoard API — руководство для тестировщика (Postman)

Документ описывает, как протестировать REST API GrowBoard из Postman: от авторизации до запуска встроенного runner'а автотестов. Рядом с этим файлом лежит готовая Postman-коллекция `growboard_postman_collection.json` — её можно импортировать одной кнопкой.

---

## 1. База, стенды и окружение

| Параметр | Значение |
|---|---|
| Production | `https://www.growboard.ru` |
| Локальный запуск (dev) | `http://localhost:5000` |
| Формат запросов/ответов | `application/json` (UTF-8) |
| Тип авторизации | JWT Bearer (flask-jwt-extended) |
| Время жизни access-токена | 365 дней (по умолчанию, см. `JWT_ACCESS_TOKEN_DAYS`) |
| CORS для `/api/*` | разрешён только `https://www.growboard.ru` |

CORS касается браузера. Из Postman кросс-оригин-ограничения не применяются, поэтому для тестов на удалённом стенде CORS мешать не должен.

### 1.1. Postman environment

Создайте окружение (Environments → Add) с переменными:

| Переменная | Initial value | Назначение |
|---|---|---|
| `base_url` | `https://www.growboard.ru` | корневой адрес |
| `access_token` | *(пусто)* | заполняется после логина |
| `invite_code` | *(пусто)* | код приглашения для регистрации |
| `team_id` | *(пусто)* | id созданной команды |
| `maturity_token` | *(пусто)* | токен ссылки зрелости |
| `survey_token` | *(пусто)* | токен публичного опроса |

Для всех защищённых запросов ставьте в Postman вкладку **Authorization → Type = Bearer Token → Token = `{{access_token}}`**. Либо добавьте заголовок вручную: `Authorization: Bearer {{access_token}}`.

---

## 2. Коды ответов и общие ошибки

| HTTP | Когда |
|---|---|
| `200` | успешный GET/POST |
| `201` | ресурс создан (команда, инвайт, roadmap и т. п.) |
| `400` | невалидный JSON / не передан обязательный параметр |
| `401` | нет/просрочен/неверный JWT, неверный логин/пароль |
| `403` | доступ запрещён (не владелец, чужая команда) |
| `404` | ресурс не найден |
| `409` | конфликт (например, команда с таким именем уже есть у пользователя) |
| `429` | исчерпан месячный AI-лимит (50 запросов / пользователь / месяц) |
| `500` | ошибка сервера (смотрите логи/трассировку) |

Типовые тела ошибок:

```json
{ "error": "Invalid credentials" }
{ "error": "Токен истёк" }
{ "error": "Достигнут лимит AI-запросов (50 за месяц). Обратитесь к администратору или дождитесь нового периода." }
```

---

## 3. Регистрация и логин (auth)

### 3.1. `POST /register`

Регистрация возможна **только по инвайт-коду**. Код генерируется другим авторизованным пользователем через `POST /api/invites`.

Запрос:

```http
POST {{base_url}}/register
Content-Type: application/json

{
  "email": "qa.tester@example.com",
  "password": "Test_Pwd_99!",
  "invite_code": "{{invite_code}}"
}
```

Возможные ответы:

- `200 OK` → `{ "message": "User registered successfully!" }`
- `400` — `Email, password and invite_code are required`, `User already exists`, `Invite code is invalid`, `Invite already used`, `Invite expired`, `Invite is bound to another email`

### 3.2. `POST /login`

```http
POST {{base_url}}/login
Content-Type: application/json

{
  "username": "qa.tester@example.com",
  "password": "Test_Pwd_99!"
}
```

Ответ:

```json
{ "access_token": "eyJhbGciOi..." }
```

**Tip (Postman Tests tab)** — автозаполнение переменной:

```javascript
const data = pm.response.json();
if (data.access_token) {
  pm.environment.set("access_token", data.access_token);
}
pm.test("Login returns token", () => pm.expect(data.access_token).to.be.a("string"));
```

Ошибка логина: `401 { "error": "Invalid credentials" }`.

### 3.3. Инвайты

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/invites` | создать инвайт (тело: `{ "invitee_email": "x@y.z", "ttl_days": 7 }`) |
| `GET`  | `/api/invites/my` | список моих инвайтов |

Ответ `POST /api/invites` (201):

```json
{
  "id": 12,
  "code": "c2f1...xyz",
  "invitee_email": "x@y.z",
  "status": "active",
  "expires_at": "2026-05-01T12:00:00Z",
  "created_at": "2026-04-21T12:00:00Z"
}
```

---

## 4. Профиль пользователя

| Метод | Путь |
|---|---|
| `GET`  | `/api/user_profile` |
| `POST` | `/api/update_profile` |

Пример запроса на обновление:

```json
{
  "full_name": "QA Tester",
  "role": "QA Engineer",
  "locale": "ru"
}
```

---

## 5. Команды и оценка зрелости (survey)

### 5.1. Создать команду

```http
POST {{base_url}}/create_team
Authorization: Bearer {{access_token}}
Content-Type: application/json

{ "team_name": "QA Team A" }
```

Ответ `201`:

```json
{ "message": "Команда создана!", "team_id": 42 }
```

Конфликт имени: `409 { "error": "Команда с таким названием уже существует" }`.

Тест-скрипт для автозаполнения переменной `team_id`:

```javascript
const data = pm.response.json();
if (data.team_id) pm.environment.set("team_id", data.team_id);
```

### 5.2. Получить список вопросов

```http
GET {{base_url}}/questions?lang=ru
```

Параметр `lang` — `ru` или `en`. Эндпоинт публичный.

### 5.3. Отправить оценку команды

```http
POST {{base_url}}/submit_assessment
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "team_id": {{team_id}},
  "answers": {
    "1": "basic",
    "2": "transitional",
    "3": "growing"
  }
}
```

Допустимые уровни: `basic`, `transitional`, `growing`, `normalization`, `optimal`. Сервер внутри переводит их в 1..5.

Ответ: `{ "message": "Результаты сохранены!", "assessment_id": 128 }`.

### 5.4. Другие полезные эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/user_teams` | мои команды |
| `GET` | `/team_progress/{team_id}` | агрегированные средние по категориям |
| `GET` | `/team_average/{team_id}` | среднее по команде |
| `GET` | `/team_results/{team_id}` | полные результаты |
| `GET` | `/team_results_history/{team_id}` | история оценок |
| `GET`/`POST` | `/assessment/{assessment_id}/recommendations` | получить/сохранить рекомендации AI (POST попадает под AI-лимит) |
| `DELETE` | `/dashboard/delete_team/{team_id}` | удалить команду |

---

## 6. Ссылки на оценку зрелости (maturity link)

Основной сценарий: менеджер создаёт токен-ссылку, раздаёт её участникам, они проходят без логина.

| Метод | Путь | Auth | Описание |
|---|---|---|---|
| `POST` | `/api/maturity-link` | JWT | создать ссылку (тело: `{ "team_id": 42, "language": "ru" }`), возвращает `token` |
| `GET` | `/api/maturity/{token}` | — | получить вопросы / состояние сессии |
| `POST` | `/api/maturity/{token}/submit` | — | отправить ответы |
| `PUT` | `/api/maturity/{token}/answers` | — | обновить ответы |
| `GET` | `/api/maturity/{token}/results` | — | результаты |
| `GET`/`POST` | `/api/maturity/{token}/recommendations` | — | получить/сгенерировать AI-рекомендации (POST = AI-лимит) |
| `GET`/`POST` | `/api/maturity/{token}/recommendations/dont-know` | — | рекомендации по «не знаю» (POST = AI-лимит) |
| `POST` | `/api/maturity/{token}/clarify` | — | уточняющий AI-вопрос (AI-лимит) |
| `GET` | `/api/maturity/{token}/team-self-link` / `POST` | JWT | команда-self-оценка: выдача/создание |
| `GET` | `/api/maturity/{token}/team-comparison` | JWT | сравнение |

Для публичных POST-ов (без JWT) AI-лимит считается по самому токену — подставляйте его в заголовок `X-Survey-Token: {{maturity_token}}` или в поле `token` тела запроса.

### 6.1. Админ-эндпоинты (под JWT владельца)

- `GET /api/maturity-admin/overview`
- `PUT /api/maturity-admin/session/{id}/group`
- `DELETE /api/maturity-admin/session/{id}`
- `GET /api/maturity-admin/session/{id}/team-comparison`
- `GET /api/maturity-admin/aggregates`
- `GET /api/maturity-admin/insights` *(AI-лимит)*
- `GET/PUT/POST /api/maturity-admin/group-plan` (POST = AI-лимит)

---

## 7. DISC-ассессмент

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/disc/questions` | список утверждений |
| `POST` | `/api/disc/submit` | отправить ответы |
| `GET` | `/api/disc/history` | моя история |
| `GET` | `/api/disc/latest` | последний профиль |

Все эндпоинты требуют JWT (кроме публичных вариантов внутри maturity-link).

Пример `POST /api/disc/submit`:

```json
{
  "answers": [
    { "question_id": 1, "type": "D" },
    { "question_id": 2, "type": "I" }
  ]
}
```

---

## 8. Инструменты для Scrum Master / PM / PO

### 8.1. Backlog preparation

| Метод | Путь |
|---|---|
| `POST` | `/prep` *(AI-лимит)* |
| `POST` | `/prep/decompose-epic` *(AI-лимит)* |
| `POST` | `/prep/assist` *(AI-лимит)* |
| `POST` | `/spec-decompose` *(AI-лимит)* |
| `GET/POST` | `/items` — CRUD |
| `GET/PUT/DELETE` | `/items/{item_id}` |
| `POST` | `/items/from-spec` |

### 8.2. Business Value

| Метод | Путь |
|---|---|
| `GET` | `/api/business-value/factors` |
| `POST` | `/api/business-value/parse-items` *(AI-лимит)* |
| `POST` | `/api/business-value/score-preview` |

### 8.3. Meeting Design

Все `POST /api/meeting-design/ai-*` и `/api/meeting-design/generate` — под AI-лимитом. CRUD по дизайну встреч: `/api/meeting-design` (GET), `/api/meeting-design/{id}` (GET/PUT/DELETE).

### 8.4. Roadmap

Префикс: не использует `/api`, маршруты как `@bp_roadmap.route("/<int:roadmap_id>", ...)` — в production пути типа `/123`, `/123/item`, `/123/item/{item_id}`, `/123/dependency`, `/123/upload-image`. Для тестирования уточните фактический префикс в `app.py` (blueprint `bp_roadmap` регистрируется без `url_prefix`).

### 8.5. Conflict

| Метод | Путь |
|---|---|
| `POST` | `/api/conflict/resolve` *(AI-лимит)* |
| `GET/POST` | `/api/conflicts` |
| `PUT/DELETE` | `/api/conflict/{id}` |
| `POST` | `/api/conflicts/save` |

### 8.6. System Thinking (iceberg)

| Метод | Путь |
|---|---|
| `POST` | `/api/system-thinking` — создать iceberg |
| `GET` | `/api/system-thinking` — список |
| `GET` | `/api/system-thinking/{id}` |
| `POST` | `/api/system-thinking/{id}/save-state` |
| `POST` | `/api/system-thinking/{id}/ask-question` |
| `POST` | `/api/system-thinking/{id}/save-level` |
| `POST` | `/api/system-thinking/{id}/generate-solutions` *(AI-лимит)* |
| `DELETE` | `/api/system-thinking/{id}` |

### 8.7. QA документы (Test Plan / Test Case)

| Метод | Путь |
|---|---|
| `POST` | `/api/qa-test-docs/plan/ai-help` *(AI-лимит)* |
| `POST` | `/api/qa-test-docs/plan/evaluate` *(AI-лимит)* |
| `POST` | `/api/qa-test-docs/plan/submit` |
| `GET/PUT/DELETE` | `/api/qa-test-docs/plan/submissions[/{id}]` |
| `POST` | `/api/qa-test-docs/case/ai-help` *(AI-лимит)* |
| `POST` | `/api/qa-test-docs/case/evaluate` *(AI-лимит)* |
| `POST` | `/api/qa-test-docs/case/submit` |
| `GET/PUT/DELETE` | `/api/qa-test-docs/case/submissions[/{id}]` |
| `POST/DELETE` | `/api/qa-test-docs/case/submissions/{id}/share` |
| `GET/PUT` | `/api/qa-test-docs/case/by-share/{token}` |

### 8.8. Interview Simulator

| Метод | Путь |
|---|---|
| `POST` | `/api/interview-simulator/question` |
| `POST` | `/api/interview-simulator/evaluate` |
| `POST` | `/api/interview-simulator/report` |
| `GET` | `/api/interview-simulator/health` |

(Точные префиксы для interview-simulator, testing-types, usability-report смотрите в `app.py` — они регистрируются без общего `/api` префикса, но внутри blueprint уже прописаны полные пути вида `/api/...`.)

### 8.9. Новые инструменты для Business Owners

| Метод | Путь |
|---|---|
| `POST` | `/api/project-card/ai-suggest` *(AI-лимит)* |
| `POST` | `/api/report-insights/analyze` *(AI-лимит)* |
| `POST` | `/api/strategy-builder/ai-suggest` *(AI-лимит)* |

Пример `POST /api/strategy-builder/ai-suggest`:

```json
{
  "section": "vision",
  "scope": "company",
  "locale": "ru",
  "industry": "финтех для розницы",
  "form": {
    "vision": "",
    "mission": "",
    "purpose": "",
    "values": [],
    "strategy": { "horizon": "", "pillars": [], "bets": [], "metrics": [] },
    "okrs": []
  }
}
```

Ответ:

```json
{ "data": { "vision": "К 2028 году мы — …" } }
```

`POST /api/report-insights/analyze` принимает либо `multipart/form-data` (поля `file` + опциональный `notes`, `locale`), либо `application/json` (`{"text": "...", "notes": "...", "locale": "ru"}`). Лимиты: файл ≤ 6 МБ, текст ≤ 30 КБ.

### 8.10. Agile Kata / Agile Tools

| Метод | Путь |
|---|---|
| `GET/POST` | `/api/agile-kata` |
| `GET/PUT/DELETE` | `/api/agile-kata/{id}` |
| `POST` | `/api/agile-kata/ai` *(AI-лимит)* |
| `GET` | `/api/agile-kata/example` |
| `POST` | `/api/agile-tools/ask` *(AI-лимит)* |

### 8.11. Planning Poker

| Метод | Путь |
|---|---|
| `POST` | `/api/planning-room` |
| `POST` | `/api/planning-room/{room_id}/add-story` |
| `GET` | `/api/planning-room/{room_id}/stories` |
| `POST` | `/api/planning-room/{room_id}/join` |
| `GET` | `/api/planning-room/{room_id}/participants` |
| `POST` | `/api/planning-room/{room_id}/vote` |
| `POST` | `/api/planning-room/{room_id}/show-votes` |
| `GET` | `/api/planning-room/{room_id}/hints` |
| `POST` | `/api/planning-room/{room_id}/leave/{participant_id}` |
| `POST` | `/api/planning-room/{room_id}/current-story` |

### 8.12. Surveys (внутренний опросник)

| Метод | Путь |
|---|---|
| `GET/POST` | `/api/surveys` |
| `PUT/DELETE` | `/api/surveys/{id}` |
| `POST` | `/api/surveys/{id}/send` |
| `GET` | `/api/surveys/{id}/results` |
| `GET` | `/api/survey/{access_token}` (public) |
| `POST` | `/api/survey/{access_token}/submit` (public) |
| `GET/POST` | `/api/survey-templates` |
| `PUT/DELETE` | `/api/survey-templates/{id}` |
| `POST` | `/api/survey-templates/ai-draft` *(AI-лимит)* |
| `GET` | `/api/employees` |

### 8.13. Community Chat

| Метод | Путь |
|---|---|
| `POST` | `/api/community-chat/presence` |
| `POST` | `/api/community-chat/resolve` |
| `GET/DELETE` | `/api/community-chat/contacts[/{user_id}]` |
| `GET` | `/api/community-chat/messages/{peer_id}` |
| `POST` | `/api/community-chat/send` |

Реал-тайм — по Socket.IO (в Postman напрямую не тестируется, используйте Postman Socket.IO request или отдельный клиент).

---

## 9. AI-лимиты и `/api/ai-usage`

- Лимит: **50 AI-запросов в месяц на пользователя** (счёт по `user:<id>`, либо по `survey:<token>` для публичных потоков, либо по `ip:<addr>` для анонимных).
- При превышении сервер возвращает `429` и тело `{ "error": "Достигнут лимит AI-запросов ..." }`.
- Проверить остаток:

```http
GET {{base_url}}/api/ai-usage
Authorization: Bearer {{access_token}}
```

Ответ:

```json
{
  "scope_key": "user:17",
  "limit": 50,
  "used": 3,
  "remaining": 47,
  "period_start": "2026-04-01T00:00:00Z"
}
```

Для тестовых прогонов рекомендую завести отдельного `qa.tester@…` чтобы не сжечь квоту продакт-пользователя.

---

## 10. Диагностика сервера

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api` | «живость»: `{ "message": "Scrum Maturity API is working!" }` |
| `GET` | `/api/ai-health` | многоуровневый health-check OpenAI (DNS → TCP → TLS → API). Возвращает `200` только если всё прошло. |

`/api/ai-health` удобен для регресс-теста после деплоя.

---

## 11. Встроенный runner автотестов

Сервер содержит собственный smoke/CRUD/i18n test-suite, который гоняет Flask test_client() изнутри (без внешнего HTTP). Идеально для QA-прогонов после релиза.

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/tests/list` | список зарегистрированных тестов по категориям |
| `POST` | `/api/tests/run` | прогнать все (или тело `{ "category": "auth" }`) |
| `POST` | `/api/tests/run/{category}` | прогнать одну категорию |

Требуют JWT.

Пример ответа `POST /api/tests/run`:

```json
{
  "total": 34,
  "passed": 32,
  "failed": 2,
  "results": [
    { "passed": true, "name": "API root responds 200", "category": "auth", "detail": "", "duration_ms": 3 },
    { "passed": false, "name": "Submit assessment with valid answers", "category": "survey", "detail": "AssertionError: expected 200", "duration_ms": 41, "traceback": "..." }
  ]
}
```

Рекомендуемые Tests-скрипты в Postman:

```javascript
pm.test("HTTP 200", () => pm.response.to.have.status(200));
const d = pm.response.json();
pm.test("No failed tests", () => pm.expect(d.failed).to.eql(0));
pm.test("Total > 0", () => pm.expect(d.total).to.be.above(0));
```

---

## 12. Практические сценарии тест-прогона

### 12.1. Smoke-прогон продакшна

1. `GET /api` → 200.
2. `GET /api/ai-health` → 200.
3. `POST /login` (техно-QA-юзер) → сохранить `access_token`.
4. `GET /api/user_profile` → 200.
5. `GET /api/ai-usage` → 200, зафиксировать `used` **до** прогона.
6. `POST /api/tests/run` → `failed = 0`.
7. `GET /api/ai-usage` → `used` не должен вырасти заметно (runner в основном не дёргает OpenAI).

### 12.2. Сценарий «новая команда + оценка»

1. `POST /create_team { "team_name": "QA_AutoTest_<timestamp>" }` → 201, сохранить `team_id`.
2. `GET /questions?lang=ru` → 200, массив вопросов (вытащить первые 3 id).
3. `POST /submit_assessment` с набором ответов → 200.
4. `GET /team_progress/{{team_id}}` → 200, массив с `average_score`.
5. `DELETE /dashboard/delete_team/{{team_id}}` → 200.

### 12.3. Сценарий «AI-инструмент для владельца»

1. `POST /api/strategy-builder/ai-suggest { "section": "vision", "scope": "team", "locale": "ru", "form": { ... } }` → 200, в ответе `data.vision` — непустая строка.
2. `POST /api/report-insights/analyze` (multipart с маленьким `.txt`) → 200, в ответе объект с `summary`, `insights[]`, `kpis[]`.
3. `GET /api/ai-usage` → `used` увеличился на 2.

### 12.4. Негативные сценарии

| Шаг | Ожидаемый ответ |
|---|---|
| `POST /login` с неверным паролем | `401 { "error": "Invalid credentials" }` |
| Любой защищённый запрос без заголовка Authorization | `401` |
| `POST /create_team` с занятым именем | `409 { "error": "Команда с таким названием уже существует" }` |
| `POST /submit_assessment` без `team_id` | `400` |
| `POST` на AI-эндпоинт после 50 запросов за месяц | `429` |
| `GET /api/maturity/invalid_token` | `404` |

---

## 13. Импорт готовой коллекции

В этой же папке лежит `growboard_postman_collection.json`. Импорт:

1. Postman → **Import** → Upload files → выбрать файл.
2. Создать новое окружение `GrowBoard — prod` с переменными из раздела 1.1.
3. Выбрать окружение в правом верхнем углу.
4. Открыть запрос **Auth → Login**, подставить свои логин/пароль, запустить — токен сохранится в переменную `access_token` автоматически (через Tests-скрипт).
5. Запускать остальные запросы.

Для регулярных регресс-прогонов используйте **Collection Runner** (значок «Run» на коллекции) или CLI `newman`:

```bash
newman run growboard_postman_collection.json \
  -e GrowBoard-prod.postman_environment.json \
  --reporters cli,junit --reporter-junit-export growboard-report.xml
```

---

## 14. Шпаргалка по полезным заголовкам

| Заголовок | Значение |
|---|---|
| `Authorization` | `Bearer {{access_token}}` — для всех защищённых ручек |
| `Content-Type` | `application/json` — для JSON-запросов |
| `Content-Type` | `multipart/form-data` — только `POST /api/report-insights/analyze` с файлом |
| `X-Survey-Token` | `{{survey_token}}` — привязка AI-лимита к публичному токену |
| `Accept-Language` | `ru` / `en` — некоторые ручки используют язык по параметру `lang`, но заголовок полезно дублировать |

---

## 15. Готовые примеры для копирования в Postman

В этом разделе — полные тела запросов и типовые ответы, которые можно вставить в Postman как есть. Переменные в фигурных скобках (`{{access_token}}`, `{{team_id}}` и т. п.) подставляются из окружения (раздел 1.1).

### 15.1. Auth

#### `POST /register`

Request (Body → raw → JSON):

```json
{
  "email": "qa.tester@example.com",
  "password": "Test_Pwd_99!",
  "invite_code": "{{invite_code}}"
}
```

Успех `200`:

```json
{ "message": "User registered successfully!" }
```

Типовые ошибки:

```json
{ "error": "Email, password and invite_code are required" }
{ "error": "User already exists" }
{ "error": "Invite code is invalid" }
{ "error": "Invite already used" }
{ "error": "Invite expired" }
{ "error": "Invite is bound to another email" }
```

#### `POST /login`

Request:

```json
{
  "username": "qa.tester@example.com",
  "password": "Test_Pwd_99!"
}
```

Успех `200`:

```json
{ "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3..." }
```

Ошибка `401`:

```json
{ "error": "Invalid credentials" }
```

Postman **Tests** для логина (сохранит токен автоматически):

```javascript
pm.test("status 200", () => pm.response.to.have.status(200));
const d = pm.response.json();
pm.test("has access_token", () => pm.expect(d.access_token).to.be.a("string"));
if (d.access_token) {
  pm.environment.set("access_token", d.access_token);
  pm.collectionVariables.set("access_token", d.access_token);
}
```

#### `POST /api/invites`

```json
{
  "invitee_email": "colleague@example.com",
  "ttl_days": 7
}
```

Успех `201`:

```json
{
  "id": 12,
  "code": "c2f1ab34567890_aB_Tq9vW",
  "invitee_email": "colleague@example.com",
  "status": "active",
  "expires_at": "2026-04-28T09:15:22Z",
  "created_at": "2026-04-21T09:15:22Z"
}
```

#### `GET /api/invites/my`

Ответ `200`:

```json
{
  "invites": [
    {
      "id": 12,
      "code": "c2f1ab34...",
      "invitee_email": "colleague@example.com",
      "status": "active",
      "expires_at": "2026-04-28T09:15:22Z",
      "created_at": "2026-04-21T09:15:22Z",
      "used_at": null,
      "used_by_user_id": null
    }
  ]
}
```

---

### 15.2. Profile

#### `GET /api/user_profile`

Ответ `200` (пример):

```json
{
  "id": 7,
  "username": "qa.tester@example.com",
  "full_name": "QA Tester",
  "role": "QA Engineer",
  "locale": "ru"
}
```

#### `POST /api/update_profile`

```json
{
  "full_name": "QA Tester",
  "role": "QA Engineer",
  "locale": "ru"
}
```

Ответ `200`:

```json
{ "message": "Profile updated" }
```

---

### 15.3. Teams & Survey

#### `POST /create_team`

```json
{ "team_name": "QA_AutoTest_{{$timestamp}}" }
```

`{{$timestamp}}` — встроенная Postman-переменная, подставляет unix-timestamp, чтобы имя всегда было уникальным.

Успех `201`:

```json
{ "message": "Команда создана!", "team_id": 42 }
```

Конфликт `409`:

```json
{ "error": "Команда с таким названием уже существует" }
```

Postman **Tests** (автосохранение `team_id`):

```javascript
pm.test("status 201", () => pm.response.to.have.status(201));
const d = pm.response.json();
if (d.team_id) pm.environment.set("team_id", d.team_id);
```

#### `POST /submit_assessment`

```json
{
  "team_id": {{team_id}},
  "answers": {
    "1": "basic",
    "2": "transitional",
    "3": "growing",
    "4": "normalization",
    "5": "optimal"
  }
}
```

Успех `200`:

```json
{ "message": "Результаты сохранены!", "assessment_id": 128 }
```

Ошибки:

```json
{ "error": "Необходимо указать команду и ответы" }
{ "error": "Некорректное значение оценки: weird_value" }
```

#### `GET /team_progress/{{team_id}}`

Ответ `200`:

```json
[
  { "category": "Планирование", "question": "Есть ли Definition of Ready?", "average_score": 3.5 },
  { "category": "Ретро", "question": "Регулярно проводим ретро?", "average_score": 4.0 }
]
```

---

### 15.4. Maturity Link

#### `POST /api/maturity-link`

```json
{
  "team_id": {{team_id}},
  "language": "ru"
}
```

Успех `201`:

```json
{
  "token": "mat_1a2b3c4d5e6f7g8h",
  "url": "https://www.growboard.ru/m/mat_1a2b3c4d5e6f7g8h",
  "team_id": 42,
  "language": "ru"
}
```

Автосохранение токена в Postman:

```javascript
const d = pm.response.json();
if (d && d.token) pm.environment.set("maturity_token", d.token);
```

#### `POST /api/maturity/{{maturity_token}}/submit`

```json
{
  "answers": {
    "1": "basic",
    "2": "transitional",
    "3": "growing"
  }
}
```

#### `POST /api/maturity/{{maturity_token}}/recommendations` *(AI-лимит)*

```json
{}
```

Рекомендуется добавить заголовок `X-Survey-Token: {{maturity_token}}`, чтобы AI-лимит считался по самой ссылке зрелости, а не по IP.

Ответ `200`:

```json
{
  "recommendations_html": "<h3>Планирование</h3><p>...</p>",
  "recommendations_plan_json": [
    {
      "category": "Планирование",
      "current_level": "transitional",
      "target_level": "growing",
      "actions": ["Ввести DoR", "Покрыть задачи критериями приёмки"]
    }
  ]
}
```

Ошибка `429` (лимит исчерпан):

```json
{ "error": "Достигнут лимит AI-запросов (50 за месяц). Обратитесь к администратору или дождитесь нового периода." }
```

---

### 15.5. DISC

#### `POST /api/disc/submit`

```json
{
  "answers": [
    { "question_id": 1, "type": "D" },
    { "question_id": 2, "type": "I" },
    { "question_id": 3, "type": "S" },
    { "question_id": 4, "type": "C" },
    { "question_id": 5, "type": "D" },
    { "question_id": 6, "type": "I" }
  ]
}
```

Ответ `200` (пример):

```json
{
  "id": 33,
  "created_at": "2026-04-21T10:00:00Z",
  "scores": { "D": 2, "I": 2, "S": 1, "C": 1 },
  "dominant_type": "D"
}
```

---

### 15.6. Business Value

#### `POST /api/business-value/score-preview`

```json
{
  "items": [
    {
      "title": "Личный кабинет клиента",
      "scores": { "revenue": 4, "risk": 2, "effort": 3, "strategy": 5 }
    },
    {
      "title": "Мобильные пуши",
      "scores": { "revenue": 3, "risk": 1, "effort": 2, "strategy": 4 }
    }
  ]
}
```

Ответ `200`:

```json
{
  "items": [
    { "title": "Личный кабинет клиента", "total": 14, "normalized": 0.78 },
    { "title": "Мобильные пуши",        "total": 10, "normalized": 0.55 }
  ]
}
```

#### `POST /api/business-value/parse-items` *(AI-лимит)*

```json
{
  "text": "1. Личный кабинет клиента\n2. Мобильные пуши\n3. Импорт из CSV\n4. Интеграция с 1C"
}
```

Ответ `200`:

```json
{
  "items": [
    { "title": "Личный кабинет клиента" },
    { "title": "Мобильные пуши" },
    { "title": "Импорт из CSV" },
    { "title": "Интеграция с 1C" }
  ]
}
```

---

### 15.7. Backlog Prep

#### `POST /api/backlog/prep/assist` *(AI-лимит)*

```json
{
  "item": {
    "title": "Онбординг нового пользователя",
    "description": "Пользователь регистрируется, проходит приветственные экраны, получает стартовые подсказки."
  },
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "suggestions": {
    "acceptance_criteria": [
      "Пользователь видит 3 приветственных экрана после регистрации",
      "Экран можно пропустить кнопкой «Пропустить»",
      "Повторный вход не показывает экраны"
    ],
    "dependencies": ["Готов шаблон email-подтверждения"],
    "risks": ["Нет метрик прохождения онбординга — сложно измерить эффект"]
  }
}
```

#### `POST /api/backlog/prep/decompose-epic` *(AI-лимит)*

```json
{
  "epic": {
    "title": "Платёжные методы для подписки",
    "description": "Добавить Apple Pay, Google Pay и SberPay; учесть возвраты и rebilling."
  },
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "stories": [
    { "title": "Подключить Apple Pay к подписке", "size": "M" },
    { "title": "Подключить Google Pay",           "size": "M" },
    { "title": "SberPay: первичная оплата",       "size": "L" },
    { "title": "Возвраты и отмены для всех методов", "size": "M" }
  ]
}
```

---

### 15.8. Project Card AI

#### `POST /api/project-card/ai-suggest` *(AI-лимит)*

```json
{
  "section": "goals",
  "locale": "ru",
  "form": {
    "projectName": "QA Pilot",
    "projectDescription": "Запуск пилота AI-тест-райтера внутри GrowBoard",
    "goals": "",
    "scope": "",
    "stakeholders": ""
  }
}
```

Другие допустимые значения `section`: `scope`, `stakeholders`, `risks`, `dependencies`, `success_criteria`, `timeline`.

Ответ `200`:

```json
{
  "data": {
    "goals": "• Запустить MVP AI-тест-райтера к концу квартала\n• Достичь 80% автогенерации Test Case из требований"
  }
}
```

---

### 15.9. Report Insights Analyzer

Поддерживает два формата: JSON (текст) и multipart (файл).

#### `POST /api/report-insights/analyze` — JSON

```json
{
  "text": "Отчёт по продажам Q1 2026. Плановая выручка: 150 млн руб. Факт: 118 млн руб. Отклонение: −21%. Количество анонимных заказов выросло с 45 до 140 в день. Средний чек анонимных заказов: 820 руб (против 3400 руб у авторизованных).",
  "notes": "Проверь рост анонимных заказов — похоже на фрод.",
  "locale": "ru"
}
```

Ответ `200` (нормализованный):

```json
{
  "data": {
    "summary": "Квартальная выручка на 21% ниже плана. Подозрительный всплеск анонимных заказов с низким чеком — вероятен фрод или сбой аутентификации.",
    "health": "red",
    "kpis": [
      { "label": "Выручка Q1",           "value": "118 млн ₽", "delta": "−21% vs план", "severity": "high" },
      { "label": "Аноним. заказы/день",  "value": "140",       "delta": "+211%",        "severity": "high" }
    ],
    "insights": [
      {
        "title": "Резкий рост анонимных заказов при низком чеке",
        "severity": "high",
        "category": "Аномалия",
        "evidence": "Анонимные 45→140/день, чек 820 ₽ (автор. 3400 ₽)",
        "why_it_matters": "Симптом фрод-волны или обхода оплаты",
        "suggested_action": "Сверить логи auth-сервиса и payment-gateway за Q1"
      }
    ],
    "questions": [
      "Когда именно начался рост анонимных заказов?",
      "Совпадают ли IP-адреса анонимных заказов?"
    ]
  }
}
```

#### `POST /api/report-insights/analyze` — multipart (file upload)

В Postman: **Body → form-data**. Поля:

| Key | Type | Value |
|---|---|---|
| `file` | File | ваш `.html` / `.pdf` / `.txt` / `.csv` / `.png` / `.jpg` |
| `notes` | Text | `Прошу обратить внимание на отклонения в Q1` |
| `locale` | Text | `ru` |

Ограничения: файл ≤ 6 МБ, сырой текст ≤ 30 КБ. Ответ — та же структура, что и в JSON-варианте.

Ошибка `413` (слишком большой файл):

```json
{ "error": "File is too large (max 6 MB)" }
```

---

### 15.10. Strategy Builder

#### `POST /api/strategy-builder/ai-suggest` — одна секция *(AI-лимит)*

```json
{
  "section": "vision",
  "scope": "company",
  "locale": "ru",
  "industry": "финтех для розницы",
  "form": {
    "vision": "",
    "mission": "",
    "purpose": "",
    "values": [],
    "strategy": { "horizon": "", "pillars": [], "bets": [], "metrics": [] },
    "okrs": []
  }
}
```

Допустимые `section`: `vision`, `mission`, `purpose`, `values`, `strategy`, `okrs`, `all`. Допустимые `scope`: `company`, `department`, `team`.

Ответ `200` для `section = "vision"`:

```json
{ "data": { "vision": "К 2028 году мы — финтех-платформа №1 в рознице, которая превращает каждую транзакцию в источник роста бизнеса клиента." } }
```

Ответ `200` для `section = "all"`:

```json
{
  "data": {
    "vision": "К 2028 году мы — …",
    "mission": "Мы помогаем розничным сетям… за счёт…",
    "purpose": "Мы верим, что платёж — это не про деньги, а про доверие.",
    "values": ["Клиент в центре", "Скорость важнее идеала", "Факты > мнения", "Безопасность по умолчанию"],
    "strategy": {
      "horizon": "2026–2028",
      "pillars": [
        { "name": "Платежи", "description": "Закрыть 95% методов оплаты в РФ" },
        { "name": "Данные",  "description": "Сделать аналитику транзакций продуктом" }
      ],
      "bets": ["Запуск Apple Pay у 50 крупнейших ритейлеров", "MVP транзакционной аналитики"],
      "metrics": ["GMV +40% YoY", "Retention партнёров ≥ 92%"]
    },
    "okrs": [
      {
        "objective": "Стать стандартом оплаты в топ-50 ритейлеров",
        "key_results": ["20 подписанных контрактов", "NPS интеграции ≥ 65", "Time-to-integrate ≤ 14 дней"]
      }
    ]
  }
}
```

---

### 15.11. Meeting Design

#### `POST /api/meeting-design/generate` *(AI-лимит)*

```json
{
  "meeting_type": "retrospective",
  "duration_minutes": 60,
  "team_size": 7,
  "context": "Команда только что зарелизила большой feature, но релиз был с инцидентом на проде.",
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "design": {
    "title": "Ретро после инцидента (60 мин, 7 человек)",
    "blocks": [
      { "name": "Set the stage", "minutes": 5,  "activity": "Check-in одним словом" },
      { "name": "Gather data",   "minutes": 15, "activity": "Timeline инцидента на доске" },
      { "name": "Generate insights", "minutes": 20, "activity": "5 почему для каждого ключевого события" },
      { "name": "Decide actions",    "minutes": 15, "activity": "SMART-экшены, владелец, дедлайн" },
      { "name": "Close",            "minutes": 5,  "activity": "ROTI + follow-up в чате" }
    ]
  }
}
```

---

### 15.12. QA Test Docs

#### `POST /api/qa-test-docs/plan/submit`

```json
{
  "fields": {
    "objectives": "Проверить регрессию релиза 2.14 и новые функции AI-отчёта",
    "scope": "Web UI (Chrome/Firefox), REST API, критичные сценарии мобильных пушей",
    "out_of_scope": "Load testing, перевод документации",
    "approach": "Exploratory + API тесты через Postman + Newman в CI",
    "entry_criteria": "Релиз-кандидат задеплоен на stage, смоук-прогон пройден",
    "exit_criteria": "0 критичных багов, coverage критичных сценариев ≥ 90%"
  }
}
```

Ответ `200`:

```json
{ "id": 17, "created_at": "2026-04-21T10:30:00Z" }
```

#### `POST /api/qa-test-docs/case/submit`

```json
{
  "fields": {
    "title": "Регистрация нового пользователя по валидному инвайту",
    "precondition": "Существует активный инвайт, пользователь не зарегистрирован",
    "steps": [
      { "action": "Открыть страницу /register", "expected": "Форма регистрации отображается" },
      { "action": "Ввести email, password и invite_code", "expected": "Кнопка «Зарегистрироваться» активна" },
      { "action": "Нажать «Зарегистрироваться»", "expected": "Редирект на /login, тост «Регистрация успешна»" }
    ],
    "priority": "high",
    "category": "auth"
  }
}
```

#### `POST /api/qa-test-docs/case/ai-help` *(AI-лимит)*

```json
{
  "context": "Тест-кейс про регистрацию по инвайту. Нужно 5 негативных сценариев.",
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "suggestions": [
    "Invalid invite_code → 400",
    "Просроченный invite_code → 400 Invite expired",
    "Уже использованный invite_code → 400 Invite already used",
    "invite_code, привязанный к другому email → 400",
    "Существующий пользователь → 400 User already exists"
  ]
}
```

---

### 15.13. Interview Simulator

#### `POST /api/interview-simulator/question`

```json
{
  "role": "frontend",
  "level": "middle",
  "job_description": "React, TypeScript, Jest, REST",
  "history": [],
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "question": "Расскажите, как вы организуете структуру папок в React-проекте среднего размера и почему.",
  "follow_up": false
}
```

#### `POST /api/interview-simulator/evaluate`

```json
{
  "role": "frontend",
  "level": "middle",
  "question": "Расскажите про мемоизацию в React.",
  "answer": "useMemo мемоизирует результат вычисления, useCallback — функцию. Использую, когда есть дорогой расчёт или когда функция передаётся в мемоизированный компонент."
}
```

Ответ `200` (пример):

```json
{
  "score": 7,
  "strengths": ["Понимает разницу useMemo/useCallback"],
  "weaknesses": ["Не упомянул deps array и typical pitfalls"],
  "follow_up_question": "А что будет, если deps массив опущен?"
}
```

---

### 15.14. Planning Poker

#### `POST /api/planning-room`

```json
{ "name": "Sprint 42 grooming", "scale": "fibonacci" }
```

Ответ `201`:

```json
{ "room_id": "pp_48dc3f", "name": "Sprint 42 grooming", "scale": "fibonacci" }
```

#### `POST /api/planning-room/{room_id}/add-story`

```json
{ "title": "Онбординг: экраны приветствия", "description": "3 экрана, skip-кнопка" }
```

#### `POST /api/planning-room/{room_id}/vote`

```json
{ "participant_id": 3, "story_id": 11, "value": "5" }
```

#### `POST /api/planning-room/{room_id}/show-votes`

```json
{ "story_id": 11 }
```

Ответ:

```json
{
  "story_id": 11,
  "votes": [
    { "participant": "Anna", "value": "5" },
    { "participant": "Pavel", "value": "3" },
    { "participant": "Maya", "value": "8" }
  ],
  "consensus": false,
  "suggested_value": "5"
}
```

---

### 15.15. Community Chat

#### `POST /api/community-chat/send`

```json
{ "peer_id": 14, "text": "Привет! Глянь, пожалуйста, PR #231." }
```

Ответ `201`:

```json
{
  "id": 902,
  "from_user_id": 7,
  "to_user_id": 14,
  "text": "Привет! Глянь, пожалуйста, PR #231.",
  "created_at": "2026-04-21T10:40:00Z",
  "read": false
}
```

---

### 15.16. Maturity admin

#### `GET /api/maturity-admin/aggregates`

Ответ `200` (пример):

```json
{
  "period_start": "2026-01-01T00:00:00Z",
  "period_end":   "2026-04-21T00:00:00Z",
  "groups": [
    {
      "group": "Платформа",
      "sessions": 14,
      "avg_score": 3.6,
      "top_gaps": ["Ретро", "Definition of Done"]
    }
  ]
}
```

#### `POST /api/maturity-admin/group-plan` *(AI-лимит)*

```json
{
  "group": "Платформа",
  "horizon_weeks": 12,
  "locale": "ru"
}
```

Ответ `200`:

```json
{
  "plan": [
    { "week": 1, "focus": "Ввести DoR",           "owner": "SM",  "metric": "% тикетов с DoR ≥ 80%" },
    { "week": 4, "focus": "Починить ретро",       "owner": "SM",  "metric": "Явка на ретро ≥ 90%" },
    { "week": 8, "focus": "Метрики исхода, не output", "owner": "PO", "metric": "OKR с outcome ≥ 3" }
  ]
}
```

---

### 15.17. AI Usage & Tests runner

#### `GET /api/ai-usage`

Ответ `200`:

```json
{
  "scope_key": "user:7",
  "limit": 50,
  "used": 12,
  "remaining": 38,
  "period_start": "2026-04-01T00:00:00Z"
}
```

#### `POST /api/tests/run`

Request:

```json
{}
```

Либо конкретная категория:

```json
{ "category": "survey" }
```

Ответ `200` (пример):

```json
{
  "total": 34,
  "passed": 34,
  "failed": 0,
  "results": [
    { "passed": true, "name": "API root responds 200",           "category": "auth",   "detail": "", "duration_ms": 3 },
    { "passed": true, "name": "Create team with valid payload",  "category": "survey", "detail": "", "duration_ms": 18 },
    { "passed": true, "name": "Submit assessment returns id",    "category": "survey", "detail": "", "duration_ms": 42 }
  ]
}
```

Postman **Tests** для CI-прогона:

```javascript
pm.test("status 200", () => pm.response.to.have.status(200));
const d = pm.response.json();
pm.test("nothing failed", () => pm.expect(d.failed).to.eql(0));
pm.test("run is non-empty", () => pm.expect(d.total).to.be.above(0));
pm.test("every test < 10s", () => {
  d.results.forEach(r => pm.expect(r.duration_ms, r.name).to.be.below(10000));
});
```

---

### 15.18. Универсальные Postman-скрипты

**Collection Pre-request Script** (проверяет, что токен есть):

```javascript
const token = pm.environment.get("access_token") || pm.collectionVariables.get("access_token");
if (!token && pm.info.requestName !== "Login (auto-save token)" && pm.info.requestName !== "Register") {
  console.warn("access_token отсутствует — сначала выполните Auth → Login");
}
```

**Глобальные Tests** (общий чек после каждого ответа):

```javascript
pm.test("Content-Type JSON", () => {
  const ct = pm.response.headers.get("Content-Type") || "";
  pm.expect(ct.toLowerCase()).to.include("application/json");
});
pm.test("не 5xx", () => {
  pm.expect(pm.response.code).to.be.below(500);
});
```

**Tests-хелпер «AI-лимит не исчерпан»** (полезно ставить перед блоком AI-запросов):

```javascript
const q = pm.response.json();
pm.test("AI quota >= 5", () => pm.expect(q.remaining).to.be.at.least(5));
```

---

### 15.19. Негативные полезные нагрузки (для проверки валидации)

#### 401 — истёкший / подделанный JWT

Header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.invalid.signature
```

Ответ:

```json
{ "error": "Недействительный токен" }
```

#### 400 — пустой JSON на `POST /create_team`

Body: `{}` → `400 { "error": "Название команды обязательно" }`.

#### 400 — неверный уровень оценки

```json
{
  "team_id": {{team_id}},
  "answers": { "1": "expert_mode" }
}
```

→ `400 { "error": "Некорректное значение оценки: expert_mode" }`.

#### 409 — дубликат команды

Дважды подряд `POST /create_team` с одинаковым `team_name` → второй раз `409 { "error": "Команда с таким названием уже существует" }`.

#### 429 — AI-лимит

Любой AI-эндпоинт после 50 запросов в календарном месяце → `429`:

```json
{ "error": "Достигнут лимит AI-запросов (50 за месяц). Обратитесь к администратору или дождитесь нового периода." }
```

Проверить заранее: `GET /api/ai-usage` → `remaining`.

---

Если найдёте расхождение между поведением и этим документом — отметьте в задаче и прислайте тело запроса/ответа: обновлю спецификацию.

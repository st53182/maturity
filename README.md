# Scrum Maturity App – дополнительные заметки

## Сборка фронта (static)

Фронт на Vue лежит в `vue-frontend/`, в прод отдаётся папка **`static/`**. После изменений в `vue-frontend` нужно каждый раз генерировать static:

```bash
cd vue-frontend && npm run build
```

Затем закоммитить изменения в `static/` и задеплоить (например, пуш в master для Render).

---

## Новая фича: подготовка бэклога с AI

- API: `POST /api/backlog/prep` — поля `text` (описание, обязательно), `work_type` (`story`/`epic`), `context` (опционально), `language` (`ru`/`en`).
- Ответ: JSON с ключами `missing_fields`, `questions`, `suggestions`, `improved_example`.
- UI: страница `Backlog Prep` в навигации (доступна после входа).

## Настройка OpenAI

1. В `.env` или переменных окружения задайте `OPENAI_API_KEY=<ваш ключ>`. **Не коммитьте ключ в репозиторий.**
2. Модель по умолчанию: `gpt-4o-mini`. Можно заменить через код, если требуется.
3. При отсутствии ключа API вернёт `OPENAI_API_KEY не задан`.

---

## Оценка зрелости по ссылке (maturity link)

- Канонический URL для участников: **`/new/maturity/{token}`** (старые `/maturity/...` редиректят на `/new/maturity/...`).
- Ответы: **да / нет / не знаю** (`dont_know` в API); на радаре «не знаю» даёт тот же балл, что «нет» (0).
- Рекомендации ИИ для пунктов «не знаю»: `POST /api/maturity/<token>/recommendations/dont-know` (кнопка на странице результатов).

### Агрегированный дашборд (только для allowlist email)

- **Канонический URL:** **`https://<хост>/new/maturity/artdash`** (нужен вход). Короткий вариант **`/new/artdash`** редиректит сюда же.
- Также: **`/maturity/artdash`** (тот же экран).
- Доступ по умолчанию: **`artem@onagile.ru`**, **`artjoms.grinakins@gmail.com`**. Если вы заходите другим email и вас перебрасывает на обычный дашборд — добавьте свой логин в env (см. ниже).
- **Render / сервер:** переменная **`MATURITY_LINK_ADMIN_EMAILS`** — список через запятую (к **базовым** двум email строки **добавляются**, не заменяют). Пример: `artem@onagile.ru,artjoms.grinakins@gmail.com,you@company.com`
- **Сборка фронта (опционально):** `VUE_APP_MATURITY_LINK_ADMIN_EMAILS` — дублирование списка для [`maturityLinkAdmin.js`](vue-frontend/src/config/maturityLinkAdmin.js), если понадобится клиентская логика; **доступ к странице решает только API** (403 при чужом email).
- API (с заголовком `Authorization: Bearer <JWT>`): `GET /api/maturity-admin/overview` (в сессиях есть полный **`token`** для ссылки на отчёт), `GET /api/maturity-admin/aggregates`, `GET /api/maturity-admin/insights`, `DELETE /api/maturity-admin/session/<id>`.
- Код: [`maturity_link.py`](maturity_link.py), [`vue-frontend/src/config/maturityLinkAdmin.js`](vue-frontend/src/config/maturityLinkAdmin.js).

### Главная страница

- **`/`** перенаправляет на **`/new`** (лендинг NewHome с входом/регистрацией).

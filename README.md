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

### Агрегированный дашборд (только для двух email)

- Страницы: **`/maturity/artdash`** или **`/new/maturity/artdash`** (нужен вход).
- Доступ: только пользователи с email **`artem@onagile.ru`** или **`artjoms.grinakins@gmail.com`** (проверка и на фронте, и на API).
- API (с заголовком `Authorization: Bearer <JWT>`): `GET /api/maturity-admin/overview`, `GET /api/maturity-admin/aggregates`, `GET /api/maturity-admin/insights`, `DELETE /api/maturity-admin/session/<id>`.
- Список email на сервере: `MATURITY_LINK_ADMIN_EMAILS` в [`maturity_link.py`](maturity_link.py); на клиенте — [`vue-frontend/src/config/maturityLinkAdmin.js`](vue-frontend/src/config/maturityLinkAdmin.js) (**держать в sync**).

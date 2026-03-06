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

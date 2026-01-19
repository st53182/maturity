# Scrum Maturity App – дополнительные заметки

## Новая фича: подготовка бэклога с AI

- API: `POST /api/backlog/prep` — поля `text` (описание, обязательно), `work_type` (`story`/`epic`), `context` (опционально), `language` (`ru`/`en`).
- Ответ: JSON с ключами `missing_fields`, `questions`, `suggestions`, `improved_example`.
- UI: страница `Backlog Prep` в навигации (доступна после входа).

## Настройка OpenAI

1. В `.env` или переменных окружения задайте `OPENAI_API_KEY=<ваш ключ>`. **Не коммитьте ключ в репозиторий.**
2. Модель по умолчанию: `gpt-4o-mini`. Можно заменить через код, если требуется.
3. При отсутствии ключа API вернёт `OPENAI_API_KEY не задан`.

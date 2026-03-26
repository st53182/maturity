-- Миграция: таблица для оценки зрелости по ссылке (да/нет, радар, PDF)
-- Запуск: psql $DATABASE_URL -f maturity_link_migration.sql

CREATE TABLE IF NOT EXISTS maturity_link_session (
    id SERIAL PRIMARY KEY,
    access_token VARCHAR(36) UNIQUE NOT NULL,
    team_name VARCHAR(255),
    group_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    answers JSONB
);

CREATE INDEX IF NOT EXISTS idx_maturity_link_session_access_token ON maturity_link_session(access_token);
CREATE INDEX IF NOT EXISTS idx_maturity_link_session_completed_at ON maturity_link_session(completed_at);

COMMENT ON TABLE maturity_link_session IS 'Оценка зрелости по ссылке: одна сессия на токен, ответы да/нет (205), радар и PDF';

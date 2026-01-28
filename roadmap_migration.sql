-- Миграция для добавления полей quarter_start и sprints_per_quarter в таблицу roadmap

-- Добавляем колонку quarter_start (формат: "2024-Q1")
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS quarter_start VARCHAR(10);

-- Добавляем колонку sprints_per_quarter с значением по умолчанию 6
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS sprints_per_quarter INTEGER DEFAULT 6;

-- Устанавливаем значение по умолчанию для существующих записей
UPDATE roadmap SET sprints_per_quarter = 6 WHERE sprints_per_quarter IS NULL;

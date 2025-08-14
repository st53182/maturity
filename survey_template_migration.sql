
CREATE TABLE survey_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    survey_type VARCHAR(50) NOT NULL,
    creator_id INTEGER REFERENCES "user"(id),
    questions JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_survey_template_creator_id ON survey_template(creator_id);
CREATE INDEX idx_survey_template_survey_type ON survey_template(survey_type);
CREATE INDEX idx_survey_template_is_default ON survey_template(is_default);

INSERT INTO survey_template (name, survey_type, creator_id, questions, is_default) VALUES 
(
    'Стандартный e-NPS опросник',
    'enps',
    NULL,
    '[
        {
            "id": 1,
            "type": "radio",
            "question": "В каком формате вы работаете?",
            "required": true,
            "options": [
                {"text": "Удаленно", "value": "remote"},
                {"text": "В офисе", "value": "office"},
                {"text": "Гибридно", "value": "hybrid"}
            ]
        },
        {
            "id": 2,
            "type": "scale",
            "question": "Насколько вы удовлетворены своей работой?",
            "required": true,
            "min": 1,
            "max": 10
        },
        {
            "id": 3,
            "type": "scale",
            "question": "Насколько вероятно, что вы порекомендуете нашу компанию как место работы друзьям или коллегам?",
            "required": true,
            "min": 0,
            "max": 10
        },
        {
            "id": 4,
            "type": "scale",
            "question": "Насколько вы удовлетворены балансом работы и личной жизни?",
            "required": true,
            "min": 1,
            "max": 10
        },
        {
            "id": 5,
            "type": "scale",
            "question": "Насколько вы удовлетворены возможностями профессионального развития?",
            "required": true,
            "min": 1,
            "max": 10
        },
        {
            "id": 6,
            "type": "scale",
            "question": "Насколько вы удовлетворены отношениями с коллегами?",
            "required": true,
            "min": 1,
            "max": 10
        },
        {
            "id": 7,
            "type": "scale",
            "question": "Насколько вы удовлетворены управлением и руководством?",
            "required": true,
            "min": 1,
            "max": 10
        },
        {
            "id": 8,
            "type": "textarea",
            "question": "Что вам больше всего нравится в работе в нашей компании?",
            "required": false
        },
        {
            "id": 9,
            "type": "textarea",
            "question": "Что бы вы хотели улучшить в нашей компании?",
            "required": false
        }
    ]'::jsonb,
    true
),
(
    'Стандартный 360° опросник',
    '360',
    NULL,
    '[
        {
            "id": 1,
            "type": "text",
            "question": "Ваше имя (необязательно)",
            "required": false
        },
        {
            "id": 2,
            "type": "text",
            "question": "Ваша роль/должность",
            "required": false
        },
        {
            "id": 3,
            "type": "radio",
            "question": "Ваши отношения с оцениваемым сотрудником",
            "required": true,
            "options": [
                {"text": "Руководитель", "value": "manager"},
                {"text": "Коллега", "value": "peer"},
                {"text": "Подчиненный", "value": "subordinate"},
                {"text": "Клиент/Партнер", "value": "external"}
            ]
        },
        {
            "id": 4,
            "type": "matrix",
            "question": "Оцените компетенции сотрудника по шкале от 1 до 5",
            "required": true,
            "rows": [
                {"text": "Профессиональные навыки", "value": "professional_skills"},
                {"text": "Коммуникация", "value": "communication"},
                {"text": "Лидерство", "value": "leadership"},
                {"text": "Работа в команде", "value": "teamwork"},
                {"text": "Решение проблем", "value": "problem_solving"},
                {"text": "Адаптивность", "value": "adaptability"}
            ],
            "columns": [
                {"text": "1 - Неудовлетворительно", "value": "1"},
                {"text": "2 - Ниже ожиданий", "value": "2"},
                {"text": "3 - Соответствует ожиданиям", "value": "3"},
                {"text": "4 - Превышает ожидания", "value": "4"},
                {"text": "5 - Выдающийся результат", "value": "5"}
            ]
        },
        {
            "id": 5,
            "type": "textarea",
            "question": "Что является главными сильными сторонами этого сотрудника?",
            "required": false
        },
        {
            "id": 6,
            "type": "textarea",
            "question": "В каких областях сотрудник мог бы улучшиться?",
            "required": false
        }
    ]'::jsonb,
    true
);

CREATE OR REPLACE FUNCTION update_survey_template_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_survey_template_updated_at
    BEFORE UPDATE ON survey_template
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_template_updated_at();

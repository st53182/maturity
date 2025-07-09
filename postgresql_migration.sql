
CREATE TABLE IF NOT EXISTS disc_assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    dominance_score INTEGER NOT NULL,
    influence_score INTEGER NOT NULL,
    steadiness_score INTEGER NOT NULL,
    conscientiousness_score INTEGER NOT NULL,
    personality_type VARCHAR(50) NOT NULL,
    recommendations TEXT,
    answers JSONB NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_disc_assessments_user_id ON disc_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_disc_assessments_completed_at ON disc_assessments(completed_at);

SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'disc_assessments' 
ORDER BY ordinal_position;

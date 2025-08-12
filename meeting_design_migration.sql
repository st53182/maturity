
CREATE TABLE IF NOT EXISTS meeting_design (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    team_id INTEGER REFERENCES team(id),
    title VARCHAR(255) NOT NULL,
    meeting_type VARCHAR(100) NOT NULL,
    goal TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    constraints TEXT,
    blocks JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_meeting_design_user_id ON meeting_design(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_design_team_id ON meeting_design(team_id);

CREATE OR REPLACE FUNCTION update_meeting_design_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_meeting_design_updated_at
    BEFORE UPDATE ON meeting_design
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_design_updated_at();

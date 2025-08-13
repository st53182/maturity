
CREATE TABLE survey (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    survey_type VARCHAR(50) NOT NULL,
    creator_id INTEGER NOT NULL REFERENCES "user"(id),
    team_id INTEGER REFERENCES team(id),
    target_employee_id INTEGER REFERENCES employee(id),
    access_token VARCHAR(36) UNIQUE NOT NULL,
    questions JSON NOT NULL,
    settings JSON,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deadline TIMESTAMP
);

CREATE TABLE survey_response (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER NOT NULL REFERENCES survey(id),
    respondent_email VARCHAR(255),
    respondent_name VARCHAR(255),
    answers JSON NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

CREATE TABLE survey_invitation (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER NOT NULL REFERENCES survey(id),
    email VARCHAR(255) NOT NULL,
    access_token VARCHAR(36) UNIQUE NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP
);

CREATE INDEX idx_survey_access_token ON survey(access_token);
CREATE INDEX idx_survey_creator_id ON survey(creator_id);
CREATE INDEX idx_survey_team_id ON survey(team_id);
CREATE INDEX idx_survey_target_employee_id ON survey(target_employee_id);
CREATE INDEX idx_survey_response_survey_id ON survey_response(survey_id);
CREATE INDEX idx_survey_invitation_survey_id ON survey_invitation(survey_id);
CREATE INDEX idx_survey_invitation_access_token ON survey_invitation(access_token);

COMMENT ON TABLE survey IS 'Stores survey definitions for both E-NPS and 360° feedback surveys';
COMMENT ON TABLE survey_response IS 'Stores individual responses to surveys';
COMMENT ON TABLE survey_invitation IS 'Stores individual invitations sent for surveys';

COMMENT ON COLUMN survey.survey_type IS 'Type of survey: enps or 360';
COMMENT ON COLUMN survey.access_token IS 'UUID token for anonymous survey access';
COMMENT ON COLUMN survey.questions IS 'JSON array of survey questions and structure';
COMMENT ON COLUMN survey.settings IS 'JSON object with survey configuration';
COMMENT ON COLUMN survey_response.answers IS 'JSON object with question_id -> answer mappings';
COMMENT ON COLUMN survey_invitation.access_token IS 'Individual UUID token for this invitation';

from database import db
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


# 🔹 Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    name = db.Column(db.String(100))
    position = db.Column(db.String(100))
    company = db.Column(db.String(100))
    personality_type = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 🔹 Модель команды
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship("Assessment", backref="team", cascade="all, delete-orphan")
    user = db.relationship('User', backref=db.backref('teams', lazy=True))

# 🔹 Модель вопросов
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False)
    subcategory = db.Column(db.String(255), nullable=False)
    question = db.Column(db.Text, nullable=False)
    
    category_en = db.Column(db.String(255), nullable=True)
    subcategory_en = db.Column(db.String(255), nullable=True)
    question_en = db.Column(db.Text, nullable=True)

    level_basic = db.Column(db.Text, nullable=True)
    level_transitional = db.Column(db.Text, nullable=True)
    level_growing = db.Column(db.Text, nullable=True)
    level_normalization = db.Column(db.Text, nullable=True)
    level_optimal = db.Column(db.Text, nullable=True)
    
    level_basic_en = db.Column(db.Text, nullable=True)
    level_transitional_en = db.Column(db.Text, nullable=True)
    level_growing_en = db.Column(db.Text, nullable=True)
    level_normalization_en = db.Column(db.Text, nullable=True)
    level_optimal_en = db.Column(db.Text, nullable=True)

# 🔹 Модель ответов пользователей
class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', backref=db.backref('assessments', lazy=True))
    question = db.relationship('Question', backref=db.backref('assessments', lazy=True))
    recommendations = db.Column(db.Text, nullable=True)
    plan = db.Column(JSON, nullable=True)

# models.py
class Conflict(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    context = db.Column(db.Text)
    participants = db.Column(db.Text)
    attempts = db.Column(db.Text)
    goal = db.Column(db.Text)
    status = db.Column(db.String(50), default="активен")
    ai_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee_1_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee_2_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    employee_1 = db.relationship('Employee', foreign_keys=[employee_1_id])
    employee_2 = db.relationship('Employee', foreign_keys=[employee_2_id])

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    stress = db.Column(db.Text)
    communication = db.Column(db.Text)
    behavior = db.Column(db.Text)
    feedback = db.Column(db.Text)
    avatar = db.Column(db.String(50), default="default.png")
    ai_analysis = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    team = db.relationship('Team', backref=db.backref('employees', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class PlanningRoom(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    show_votes = db.Column(db.Boolean, default=False)

    participants = db.relationship('Participant', backref='planning_room', cascade="all, delete-orphan")
    votes = db.relationship('Vote', backref='planning_room', cascade="all, delete-orphan")

    # 👇 ЯВНО УКАЗАЛ foreign_keys, чтобы убрать конфликт
    stories = db.relationship(
        'PokerStory',
        backref='planning_room',
        cascade="all, delete-orphan",
        foreign_keys='PokerStory.room_id'
    )

    current_story_id = db.Column(db.Integer, db.ForeignKey('poker_story.id'), nullable=True)
    current_story = db.relationship(
        'PokerStory',
        foreign_keys=[current_story_id]
    )




# 🔹 Участник сессии
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    room_id = db.Column(db.String(36), db.ForeignKey('planning_room.id'), nullable=False)

    votes = db.relationship('Vote', backref='participant', cascade="all, delete-orphan")


# 🔹 Голос / оценка участника

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('poker_story.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    room_id = db.Column(db.String(36), db.ForeignKey('planning_room.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PokerStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('planning_room.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    votes = db.relationship('Vote', backref='story', cascade="all, delete-orphan")

class DISCAssessment(db.Model):
    __tablename__ = 'disc_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dominance_score = db.Column(db.Integer, nullable=False)
    influence_score = db.Column(db.Integer, nullable=False)
    steadiness_score = db.Column(db.Integer, nullable=False)
    conscientiousness_score = db.Column(db.Integer, nullable=False)
    personality_type = db.Column(db.String(50), nullable=False)
    recommendations = db.Column(db.Text, nullable=True)
    answers = db.Column(JSON, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('disc_assessments', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'dominance_score': self.dominance_score,
            'influence_score': self.influence_score,
            'steadiness_score': self.steadiness_score,
            'conscientiousness_score': self.conscientiousness_score,
            'personality_type': self.personality_type,
            'recommendations': self.recommendations,
            'answers': self.answers,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    survey_type = db.Column(db.String(50), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    target_employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    access_token = db.Column(db.String(36), unique=True, nullable=False)
    questions = db.Column(JSON, nullable=False)
    settings = db.Column(JSON, nullable=True)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    
    creator = db.relationship('User', backref=db.backref('created_surveys', lazy=True))
    team = db.relationship('Team', backref=db.backref('surveys', lazy=True))
    target_employee = db.relationship('Employee', backref=db.backref('feedback_surveys', lazy=True))
    responses = db.relationship('SurveyResponse', backref='survey', cascade="all, delete-orphan")

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    respondent_email = db.Column(db.String(255), nullable=True)
    respondent_name = db.Column(db.String(255), nullable=True)
    answers = db.Column(JSON, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)

class SurveyInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    access_token = db.Column(db.String(36), unique=True, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    survey = db.relationship('Survey', backref=db.backref('invitations', lazy=True))

class MeetingDesign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    meeting_type = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.Text, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    constraints = db.Column(db.Text, nullable=True)
    blocks = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('meeting_designs', lazy=True))
    team = db.relationship('Team', backref=db.backref('meeting_designs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'title': self.title,
            'meeting_type': self.meeting_type,
            'goal': self.goal,
            'duration_minutes': self.duration_minutes,
            'constraints': self.constraints,
            'blocks': self.blocks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SurveyTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    survey_type = db.Column(db.String(50), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    questions = db.Column(JSON, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref=db.backref('survey_templates', lazy=True))

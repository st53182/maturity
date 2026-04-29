from database import db
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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


class UserInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), unique=True, nullable=False, index=True)
    inviter_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invitee_email = db.Column(db.String(255), nullable=True)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="active")
    max_uses = db.Column(db.Integer, nullable=False, default=1)
    use_count = db.Column(db.Integer, nullable=False, default=0)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=7))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)

    inviter = db.relationship('User', foreign_keys=[inviter_user_id], backref=db.backref('sent_invites', lazy=True))
    used_by = db.relationship('User', foreign_keys=[used_by_user_id], backref=db.backref('accepted_invites', lazy=True))


class AiUsageCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope_key = db.Column(db.String(255), nullable=False, index=True)
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    count = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('scope_key', 'period_start', name='uq_ai_usage_scope_period'),)

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


# 🔹 Оценка зрелости по ссылке (пять вариантов ответа, радар, PDF)
class MaturityLinkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(36), unique=True, nullable=False)
    team_access_token = db.Column(db.String(36), unique=True, nullable=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    team_name = db.Column(db.String(255), nullable=True)
    group_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    survey_locale = db.Column(db.String(5), nullable=True)  # 'ru' | 'en' — язык текста вопросов (после менеджера — для командной ссылки)
    answers = db.Column(JSON, nullable=True)  # список ответов по индексу (строки no/rather_no/dont_know/rather_yes/yes)
    recommendations_html = db.Column(db.Text, nullable=True)
    dont_know_recommendations_html = db.Column(db.Text, nullable=True)
    recommendations_plan_json = db.Column(JSON, nullable=True)
    dont_know_recommendations_plan_json = db.Column(JSON, nullable=True)

    link_creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('maturity_link_sessions_created', lazy='dynamic'))


class MaturityTeamSelfSubmission(db.Model):
    """Анонимные самооценки команды по общей ссылке (несколько строк на одну менеджерскую сессию)."""
    __tablename__ = 'maturity_team_self_submission'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('maturity_link_session.id', ondelete='CASCADE'), nullable=False, index=True)
    answers = db.Column(JSON, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('MaturityLinkSession', backref=db.backref('team_self_submissions', lazy='dynamic'))


class MaturityGroupPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), nullable=False, unique=True)
    plan_json = db.Column(JSON, nullable=False)
    plan_html = db.Column(db.Text, nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 🔹 Модель дорожной карты зависимостей
class Roadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_token = db.Column(db.String(36), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    quarter_start = db.Column(db.String(10), nullable=True)  # Формат: "2024-Q1"
    sprints_per_quarter = db.Column(db.Integer, default=6)  # Количество спринтов в квартале
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref=db.backref('roadmaps', lazy=True))
    items = db.relationship('RoadmapItem', backref='roadmap', cascade='all, delete-orphan', lazy=True)
    
    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

# 🔹 Модель элемента дорожной карты (эпик/история)
class RoadmapItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmap.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'epic' или 'story'
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position_x = db.Column(db.Float, default=0.0)
    position_y = db.Column(db.Float, default=0.0)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    # Опционально для таймлайна /roadmap: stream (str), start/end (ISO date YYYY-MM-DD)
    item_metadata = db.Column(JSON, nullable=True)  # Дополнительные данные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    team = db.relationship('Team', backref=db.backref('roadmap_items', lazy=True))
    dependencies_from = db.relationship('RoadmapDependency', foreign_keys='RoadmapDependency.from_item_id', backref='from_item', cascade='all, delete-orphan', lazy=True)
    dependencies_to = db.relationship('RoadmapDependency', foreign_keys='RoadmapDependency.to_item_id', backref='to_item', cascade='all, delete-orphan', lazy=True)

# 🔹 Модель зависимости между элементами
class RoadmapDependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_item_id = db.Column(db.Integer, db.ForeignKey('roadmap_item.id'), nullable=False)
    to_item_id = db.Column(db.Integer, db.ForeignKey('roadmap_item.id'), nullable=False)
    dependency_type = db.Column(db.String(50), nullable=False)  # 'blocks', 'depends_on', 'related_to', 'requires', 'precedes', 'follows'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('from_item_id', 'to_item_id', name='unique_dependency'),)

# 🔹 Модель доступа пользователей к дорожной карте
class RoadmapAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmap.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_level = db.Column(db.String(50), default='viewer')  # 'viewer', 'editor', 'owner'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    roadmap = db.relationship('Roadmap', backref=db.backref('accesses', lazy=True))
    user = db.relationship('User', backref=db.backref('roadmap_accesses', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('roadmap_id', 'user_id', name='unique_roadmap_access'),)

class SystemThinkingIceberg(db.Model):
    """Модель для айсберга системного мышления"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Уровни айсберга
    event = db.Column(db.Text, nullable=True)  # Событие
    pattern = db.Column(db.Text, nullable=True)  # Паттерн поведения
    system_structure = db.Column(db.Text, nullable=True)  # Системная структура
    mental_model = db.Column(db.Text, nullable=True)  # Ментальная модель
    experience = db.Column(db.Text, nullable=True)  # Опыт
    
    # Решения
    solutions = db.Column(JSON, nullable=True)  # Массив решений на трех уровнях
    
    # Статус заполнения
    current_level = db.Column(db.String(50), default='event')  # event, pattern, system_structure, mental_model, experience, completed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('system_thinking_icebergs', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event': self.event,
            'pattern': self.pattern,
            'system_structure': self.system_structure,
            'mental_model': self.mental_model,
            'experience': self.experience,
            'solutions': self.solutions,
            'current_level': self.current_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AgileKataCanvas(db.Model):
    """Интерактивный Agile Kata Canvas (системное улучшение через эксперименты)."""
    __tablename__ = "agile_kata_canvas"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False, default="Agile Kata")
    canvas_state = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("agile_kata_canvases", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "canvas_state": self.canvas_state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QAUserStorySubmission(db.Model):
    """Пул разработки: пользовательские истории и критерии приёмки (QA задание 5)."""
    __tablename__ = 'qa_user_story_submissions'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    team_name = db.Column(db.String(255), nullable=False, default='')
    user_story = db.Column(db.Text, nullable=False, default='')
    acceptance_criteria = db.Column(db.Text, nullable=False, default='[]')  # JSON array of strings
    score = db.Column(db.Integer, nullable=True)
    ac_count = db.Column(db.Integer, nullable=True)


class QATestPlanSubmission(db.Model):
    """QA задание 6: сохраненные test plan документы пользователя."""
    __tablename__ = "qa_test_plan_submissions"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    team_name = db.Column(db.String(255), nullable=True)
    payload_json = db.Column(JSON, nullable=False)
    quality_score = db.Column(db.Integer, nullable=True)
    quality_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", backref=db.backref("qa_test_plan_submissions", lazy=True))


class QATestCaseSubmission(db.Model):
    """QA задание 7: сохраненные test case документы пользователя."""
    __tablename__ = "qa_test_case_submissions"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    team_name = db.Column(db.String(255), nullable=True)
    payload_json = db.Column(JSON, nullable=False)
    quality_score = db.Column(db.Integer, nullable=True)
    quality_feedback = db.Column(db.Text, nullable=True)
    share_token = db.Column(db.String(64), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", backref=db.backref("qa_test_case_submissions", lazy=True))


class BacklogWorkItem(db.Model):
    """Эпики и истории подготовки бэклога (PO): хранение, декомпозиция, экспорт в Jira."""

    __tablename__ = "backlog_work_item"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("backlog_work_item.id"), nullable=True, index=True)
    item_type = db.Column(db.String(20), nullable=False)  # epic | story

    title = db.Column(db.String(500), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    acceptance_criteria = db.Column(db.Text, nullable=True)
    nfr = db.Column(db.Text, nullable=True)
    context = db.Column(db.Text, nullable=True)
    decomposition_suggestions = db.Column(JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("backlog_work_items", lazy=True))
    children = db.relationship(
        "BacklogWorkItem",
        backref=db.backref("parent", remote_side=[id]),
    )

    def to_dict(self, include_children: bool = False):
        out = {
            "id": self.id,
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "item_type": self.item_type,
            "title": self.title or "",
            "description": self.description or "",
            "acceptance_criteria": self.acceptance_criteria or "",
            "nfr": self.nfr or "",
            "context": self.context or "",
            "decomposition_suggestions": self.decomposition_suggestions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_children:
            ch = sorted(self.children, key=lambda c: c.id)
            out["children"] = [c.to_dict(include_children=False) for c in ch]
        return out


class DirectMessage(db.Model):
    """Личные сообщения между пользователями (username = email в системе)."""

    __tablename__ = "direct_message"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_direct_messages", lazy="dynamic"))
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref=db.backref("received_direct_messages", lazy="dynamic"))


class ChatContact(db.Model):
    """Сохранённые контакты для чата: пользователь A ведёт список собеседников по e-mail."""

    __tablename__ = "chat_contact"
    __table_args__ = (
        db.UniqueConstraint("user_id", "contact_user_id", name="uq_chat_contact_owner_peer"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    contact_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", foreign_keys=[user_id], backref=db.backref("chat_contacts_owned", lazy="dynamic"))
    contact = db.relationship("User", foreign_keys=[contact_user_id], backref=db.backref("chat_contacts_as_target", lazy="dynamic"))


class AgileTrainingSession(db.Model):
    """Сессия тренинга по Agile (владелец = фасилитатор)."""

    __tablename__ = "agile_training_session"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, default="Agile training")
    exercise_key = db.Column(db.String(64), nullable=False, default="agile_principles", index=True)
    locale = db.Column(db.String(8), nullable=False, default="ru")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", backref=db.backref("agile_training_sessions", lazy="dynamic"))
    groups = db.relationship(
        "AgileTrainingGroup",
        backref="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class AgileTrainingGroup(db.Model):
    """Команда внутри тренинга; slug — часть публичной ссылки /g/<slug>."""

    __tablename__ = "agile_training_group"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False, default="Team")
    slug = db.Column(db.String(96), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    participants = db.relationship(
        "AgileTrainingParticipant",
        backref="group",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    answers = db.relationship(
        "AgileTrainingAnswer",
        backref="group",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class AgileTrainingParticipant(db.Model):
    """Участник тренинга без логина; идентифицируется непубличным токеном в localStorage."""

    __tablename__ = "agile_training_participant"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    answers = db.relationship(
        "AgileTrainingAnswer",
        backref="participant",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class AgileTrainingAnswer(db.Model):
    """Ответ участника по одному принципу."""

    __tablename__ = "agile_training_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id", "principle_key", name="uq_agile_training_answer_participant_principle"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    principle_key = db.Column(db.String(64), nullable=False, index=True)
    value = db.Column(db.String(16), nullable=False)  # relevant | outdated
    rewrite = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AgileTrainingCynefinAnswer(db.Model):
    """Ответ участника по одному кейсу Cynefin (домен + стратегия)."""

    __tablename__ = "agile_training_cynefin_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id", "case_key",
            name="uq_cynefin_answer_participant_case",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_key = db.Column(db.String(64), nullable=False, index=True)
    selected_domain = db.Column(db.String(32), nullable=False)
    selected_strategy = db.Column(db.String(64), nullable=True)
    custom_strategy = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AgileTrainingIcebergAnswer(db.Model):
    """Ответ участника по одному кейсу упражнения «Айсберг».

    В отличие от принципов / Cynefin у нас не один атом ответа, а
    комплексный: размещения карточек по уровням, классификация
    поверхностных объяснений, причинная цепочка, интервенции.
    Храним всё в JSON-поле `data_json`, чтобы не плодить таблицы.
    """

    __tablename__ = "agile_training_iceberg_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id", "case_key",
            name="uq_iceberg_answer_participant_case",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_key = db.Column(db.String(64), nullable=False, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    depth_score = db.Column(db.Integer, nullable=False, default=0)
    primary_level = db.Column(db.String(32), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AgileTrainingMvpAnswer(db.Model):
    """Ответ участника по одному кейсу MVP→MMP→MLP.

    Храним один общий JSON на кейс с выборами участника на каждой итерации
    и вычисленными статусами — так удобнее поднимать последнее состояние
    на фронте при возврате на страницу."""

    __tablename__ = "agile_training_mvp_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id", "case_key",
            name="uq_mvp_answer_participant_case",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_key = db.Column(db.String(64), nullable=False, index=True)
    # Структура:
    # {
    #   "mvp": { "features": ["f1","f2"], "status": "partial" },
    #   "mmp": { "features": [...], "status": "success" },
    #   "mlp": { "features": [...], "status": "success" }
    # }
    data_json = db.Column(db.Text, nullable=False, default="{}")
    total_score = db.Column(db.Integer, nullable=False, default=0)
    final_stage = db.Column(db.String(16), nullable=True, index=True)  # mvp | mmp | mlp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingDorDodAnswer(db.Model):
    """Ответ участника тренажёра Definition of Ready / Definition of Done.

    Модель простая: один участник — одна запись в группе. Внутри
    `data_json` хранятся обе итерации (initial и improved) и выбранный
    тип команды, чтобы можно было показать «стало лучше или нет»."""

    __tablename__ = "agile_training_dor_dod_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_dor_dod_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_key = db.Column(db.String(32), nullable=False, index=True)
    # Структура:
    # {
    #   "initial":  { "dor": [...], "dod": [...], "mapping": {rule: [effects]} },
    #   "improved": { ... } | null,
    #   "eval_initial":  { ...evaluate_round output... },
    #   "eval_improved": { ... } | null
    # }
    data_json = db.Column(db.Text, nullable=False, default="{}")
    score_initial = db.Column(db.Float, nullable=False, default=0.0)
    score_improved = db.Column(db.Float, nullable=True)
    outcome_initial = db.Column(db.String(32), nullable=True)
    outcome_improved = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingWsjfAnswer(db.Model):
    """Ответ участника тренажёра WSJF-приоритизации.

    Одна запись на участника. `data_json` хранит оба раунда — initial и
    revised — с их scores, choice, wsjf, errors. Отдельные колонки
    дублируют ключевые поля для быстрых выборок."""

    __tablename__ = "agile_training_wsjf_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_wsjf_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_key = db.Column(db.String(32), nullable=False, index=True)
    event_key = db.Column(db.String(64), nullable=True, index=True)
    initial_choice = db.Column(db.String(32), nullable=True, index=True)
    revised_choice = db.Column(db.String(32), nullable=True, index=True)
    adaptation = db.Column(db.String(32), nullable=True, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingRiceAnswer(db.Model):
    """Ответ участника тренажёра RICE-приоритизации.

    По структуре повторяет WSJF: одна запись на участника с двумя раундами
    (initial/revised) в `data_json` и ключевыми полями в колонках.
    """

    __tablename__ = "agile_training_rice_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_rice_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_key = db.Column(db.String(32), nullable=False, index=True)
    event_key = db.Column(db.String(64), nullable=True, index=True)
    initial_choice = db.Column(db.String(32), nullable=True, index=True)
    revised_choice = db.Column(db.String(32), nullable=True, index=True)
    adaptation = db.Column(db.String(32), nullable=True, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingScrumRolesAnswer(db.Model):
    """Ответ участника тренажёра «Роли в Scrum».

    Одна запись на участника. `data_json` хранит весь выбор:
    selection[card_key][role_key] = level ('responsible' | 'participates' |
    'should_not' | null), errors_seen, custom_cards, custom_role и
    evaluation."""

    __tablename__ = "agile_training_scrum_roles_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_scrum_roles_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = db.Column(db.Integer, nullable=True, index=True)
    max_score = db.Column(db.Integer, nullable=True)
    health_pct = db.Column(db.Integer, nullable=True, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingRoleQuizAnswer(db.Model):
    """Ответ участника тренажёра «Кто отвечает?» (RACI-квиз по ситуациям).

    Одна запись на участника. `data_json` хранит:
      - selection[situation_key][role_key] = level | null
      - evaluation: подробная разбивка по эталону
      - notes_seen: типовые ошибки, которые показали участнику
    """

    __tablename__ = "agile_training_role_quiz_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_role_quiz_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = db.Column(db.Integer, nullable=True, index=True)
    max_score = db.Column(db.Integer, nullable=True)
    health_pct = db.Column(db.Integer, nullable=True, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingScrumEventsAnswer(db.Model):
    """Ответ участника тренажёра Scrum events / «Ритм работы команды».

    Одна запись на участника. `data_json` хранит весь выбор:
    selection[stage][category] = [card_keys], evaluation, errors,
    custom-режим (если собран)."""

    __tablename__ = "agile_training_scrum_events_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_scrum_events_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = db.Column(db.Integer, nullable=True, index=True)
    max_score = db.Column(db.Integer, nullable=True)
    health_pct = db.Column(db.Integer, nullable=True, index=True)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingProductThinkingAnswer(db.Model):
    """Ответ участника тренинга «Продуктовое мышление: User Story / Job Story / декомпозиция».

    Одна запись на участника. `data_json` хранит весь артефакт:
    user_story, job_story, epic_summary, tasks[], improved_tasks[],
    chosen_technique ('spidr' | 'seven_dim' | null), notes по экранам,
    history AI-помощника и счётчик AI-обращений для лимита.
    """

    __tablename__ = "agile_training_product_thinking_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_product_thinking_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = db.Column(db.String(32), nullable=True, index=True)
    user_story = db.Column(db.Text, nullable=True)
    job_story = db.Column(db.Text, nullable=True)
    tasks_count = db.Column(db.Integer, nullable=True, index=True)
    chosen_technique = db.Column(db.String(16), nullable=True, index=True)
    ai_calls = db.Column(db.Integer, nullable=False, default=0)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingKanbanAnswer(db.Model):
    """Ответ участника тренинга «Kanban-система и системное мышление».

    Одна запись на участника. Весь артефакт хранится в `data_json`:
    case_key, dissatisfaction, demand[], workflow[], classes[], policies[],
    cadences{}, swimlanes[], column_limits{}, cards[], improved_board,
    notes, ai_history, счётчик AI-обращений.
    """

    __tablename__ = "agile_training_kanban_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_kanban_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = db.Column(db.String(32), nullable=True, index=True)
    case_key = db.Column(db.String(32), nullable=True, index=True)
    cards_count = db.Column(db.Integer, nullable=True, index=True)
    columns_count = db.Column(db.Integer, nullable=True, index=True)
    swimlanes_count = db.Column(db.Integer, nullable=True, index=True)
    ai_calls = db.Column(db.Integer, nullable=False, default=0)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingScrumSimState(db.Model):
    """Общее состояние симулятора Scrum для всей команды (одна запись на группу).

    Multiplayer-тренажёр: действия любого участника меняют эту одну запись
    через серверные эндпоинты, а клиенты опрашивают `/state` для синхронизации.
    Весь игровой артефакт хранится в `data_json`:
      phase ("lobby" | "planning" | "day_1..day_5" | "review" | "retro" | "summary"),
      current_day, team_capacity_per_day, sprint_goal,
      product_backlog[], sprint_backlog[], tasks{id: {...}},
      days[] (история шагов), roles{token: role}, participants{token: {...}},
      event_queue[], retro_picks[], review_metrics{}, notes{}, ai_calls{token: n}.
    """

    __tablename__ = "agile_training_scrum_sim_state"
    __table_args__ = (
        db.UniqueConstraint("group_id", name="uq_scrum_sim_state_group"),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase = db.Column(db.String(32), nullable=False, default="lobby")
    current_day = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=0)
    paused = db.Column(db.Boolean, nullable=False, default=False)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingPoPathAnswer(db.Model):
    """Ответ участника тренинга «Путь Product Owner: JTBD → Value → Market Fit → Lean Canvas».

    Многоэтапный воркшоп с фасилитатором. Одна запись на участника.
    Структура `data_json`:
      {
        "current_stage": "jtbd"|"value"|"fit"|"canvas"|"done",
        "stages": {
          "jtbd":   {"status": "draft|submitted|in_review|approved|needs_revision",
                     "data":   {...поля этапа...},
                     "confidence": 0..5 | null,
                     "comments": [{"author":"facilitator|self", "text": "...", "ts": iso, "kind": "review|note"}],
                     "submitted_at": iso|null,
                     "approved_at":  iso|null,
                     "review_round": 0..N},
          "value":  {...},
          "fit":    {..., "ai_questions": [{"q":"...","answer":"..."}]},
          "canvas": {...}
        },
        "ai_history": [{"mode": "...","input":"...","reply":"...","ts":iso}],
        "ai_calls":   N
      }
    """

    __tablename__ = "agile_training_po_path_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_po_path_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_stage = db.Column(db.String(16), nullable=False, default="jtbd", index=True)
    overall_status = db.Column(db.String(16), nullable=True, index=True)  # quick filter for facilitator
    stages_completed = db.Column(db.Integer, nullable=False, default=0, index=True)
    ai_calls = db.Column(db.Integer, nullable=False, default=0)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingPmSimState(db.Model):
    """Командный продуктовый симулятор Product Owner на 20 недель.

    Multiplayer-тренажёр: одна запись на группу = одна «команда», все участники
    видят один общий дашборд и голосуют за решения; PO подтверждает выбор.
    Весь игровой артефакт хранится в `data_json` (см. agile_pm_sim._initial_state).
    """

    __tablename__ = "agile_training_pm_sim_state"
    __table_args__ = (
        db.UniqueConstraint("group_id", name="uq_pm_sim_state_group"),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase = db.Column(db.String(32), nullable=False, default="lobby", index=True)
    current_week = db.Column(db.Integer, nullable=False, default=0, index=True)
    status = db.Column(db.String(16), nullable=False, default="alive", index=True)
    revenue_total = db.Column(db.Integer, nullable=False, default=0, index=True)
    version = db.Column(db.Integer, nullable=False, default=0)
    paused = db.Column(db.Boolean, nullable=False, default=False)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingStakeholderMatrixAnswer(db.Model):
    """Тренажёр «Матрица стейкхолдеров» (влияние × заинтересованность, 3×3).

    Одна запись на участника. `data_json`: расстановка ролей, ответы на вопросы
    обсуждения, стратегии по квадрантам, второй раунд, AI-история, счётчик AI.
    """

    __tablename__ = "agile_training_stakeholder_matrix_answer"
    __table_args__ = (
        db.UniqueConstraint(
            "participant_id",
            name="uq_stakeholder_matrix_answer_participant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    screen = db.Column(db.String(32), nullable=True, index=True)
    ai_calls = db.Column(db.Integer, nullable=False, default=0)
    data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgileTrainingRewriteSuggestion(db.Model):
    """Коллективные предложения по переформулировке принципа внутри одной группы.

    В отличие от Answer.rewrite (один на ответ), таких предложений может быть
    несколько от одного участника и по одному принципу — чтобы команда могла
    обсуждать и дорабатывать формулировки прямо на экране результатов.
    """

    __tablename__ = "agile_training_rewrite_suggestion"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("agile_training_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    principle_key = db.Column(db.String(64), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    participant = db.relationship("AgileTrainingParticipant")
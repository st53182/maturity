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

    level_basic = db.Column(db.Text, nullable=True)
    level_transitional = db.Column(db.Text, nullable=True)
    level_growing = db.Column(db.Text, nullable=True)
    level_normalization = db.Column(db.Text, nullable=True)
    level_optimal = db.Column(db.Text, nullable=True)

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
    stories = db.relationship('PokerStory', backref='planning_room', cascade="all, delete-orphan")



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
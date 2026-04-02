from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from database import db
from survey import bp_survey
from auth import bp_auth
from dashboard import bp_dashboard
from assessment import bp_assessment
from datetime import timedelta
import os
from flask_cors import CORS
from conflict import bp_conflict
from motivation import bp_motivation
from user_profile import profile_bp
from planning_poker import planning_bp
from disc_assessment import disc_bp
from meeting_design import bp_meeting_design
from surveys import surveys_bp
from maturity_link import maturity_bp
from backlog_prep import bp_backlog_prep
from roadmap import bp_roadmap, init_socketio, register_socketio_handlers
from community_chat import bp_community_chat, register_community_socketio_handlers
from system_thinking import bp_system_thinking
from agile_kata import bp_agile_kata
from agile_tools_ai import bp_agile_tools_ai
from testing_types import bp_testing_types
from usability_report import bp_usability_report
from qa_user_story import bp_qa_user_story
from qa_test_docs import bp_qa_test_docs
from flask_socketio import SocketIO
from ai_limits import bp_ai_limits, register_ai_limit_hooks, AiLimitExceeded

app = Flask(__name__, static_folder="static")
CORS(app, supports_credentials=True)
CORS(app, resources={r"/api/*": {"origins": "https://www.growboard.ru"}}, supports_credentials=True)



# 📦 Подключение к базе данных
database_url = os.getenv("DATABASE_URL", "sqlite:///maturity_local.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if database_url.startswith("sqlite"):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c timezone=utc"
        }
    }

# JWT
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=730)

# Инициализация
db.init_app(app)
jwt = JWTManager(app)

# Инициализация SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
init_socketio(socketio)
register_socketio_handlers(socketio)

with app.app_context():
    db.create_all()
    # Добавление колонки для существующих БД (create_all не меняет таблицы)
    from sqlalchemy import text
    try:
        db.session.execute(
            text("ALTER TABLE qa_test_case_submissions ADD COLUMN share_token VARCHAR(64)")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_qa_test_case_submissions_share_token "
                "ON qa_test_case_submissions (share_token)"
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN recommendations_html TEXT")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN dont_know_recommendations_html TEXT")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN recommendations_plan_json JSON")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(
            text("ALTER TABLE maturity_link_session ADD COLUMN dont_know_recommendations_plan_json JSON")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

register_ai_limit_hooks(app)

# Blueprints
app.register_blueprint(bp_auth)
app.register_blueprint(bp_survey)
app.register_blueprint(bp_dashboard, url_prefix="/dashboard")
app.register_blueprint(bp_assessment)
app.register_blueprint(bp_conflict, url_prefix="/api")

app.register_blueprint(bp_motivation)

app.register_blueprint(profile_bp, url_prefix="/api")
app.register_blueprint(planning_bp, url_prefix="/api")
app.register_blueprint(disc_bp, url_prefix="/api/disc")
app.register_blueprint(bp_meeting_design)
app.register_blueprint(surveys_bp, url_prefix="/api")
app.register_blueprint(maturity_bp)
app.register_blueprint(bp_backlog_prep)
app.register_blueprint(bp_roadmap)
app.register_blueprint(bp_community_chat)
app.register_blueprint(bp_system_thinking)
app.register_blueprint(bp_agile_kata)
app.register_blueprint(bp_agile_tools_ai)
app.register_blueprint(bp_testing_types)
app.register_blueprint(bp_usability_report)
app.register_blueprint(bp_qa_user_story)
app.register_blueprint(bp_qa_test_docs)
app.register_blueprint(bp_ai_limits)


@app.errorhandler(AiLimitExceeded)
def handle_ai_limit_exceeded(e):
    return jsonify({"error": e.message}), 429


# 🎯 Отдача Vue SPA
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return send_from_directory("static", "index.html")

@app.route("/api")
def api_root():
    return {"message": "Scrum Maturity API is working!"}

# Экспортируем socketio для использования в gunicorn
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)


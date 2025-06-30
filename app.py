from flask import Flask, send_from_directory
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


app = Flask(__name__, static_folder="static")
CORS(app, supports_credentials=True)



# 📦 Подключение к базе данных
database_url = os.getenv("DATABASE_URL", "postgresql://localhost/fallback_db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

with app.app_context():
    db.create_all()

# Blueprints
app.register_blueprint(bp_auth)
app.register_blueprint(bp_survey)
app.register_blueprint(bp_dashboard, url_prefix="/dashboard")
app.register_blueprint(bp_assessment)
app.register_blueprint(bp_conflict, url_prefix="/api")

app.register_blueprint(bp_motivation)

app.register_blueprint(profile_bp)


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

if __name__ == '__main__':
    app.run()


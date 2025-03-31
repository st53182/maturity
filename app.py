from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from database import db
from survey import bp_survey
from auth import bp_auth
from dashboard import bp_dashboard
from assessment import bp_assessment
from datetime import timedelta
import os

app = Flask(__name__, static_folder="static")

# CORS
from flask_cors import CORS
CORS(app, supports_credentials=True)

# 🔗 Подключение к PostgreSQL через переменную окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://localhost/fallback_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=730)

# Инициализация
db.init_app(app)
jwt = JWTManager(app)

# Регистрация blueprint'ов
app.register_blueprint(bp_auth)
app.register_blueprint(bp_survey)
app.register_blueprint(bp_dashboard, url_prefix="/dashboard")
app.register_blueprint(bp_assessment)

# Отдача фронтенда
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return send_from_directory("static", "index.html")

# API-заглушка
@app.route("/api")
def api_root():
    return {"message": "Scrum Maturity API is working!"}

if __name__ == '__main__':
    app.run()

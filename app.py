from flask import Flask
from flask_jwt_extended import JWTManager
from database import db
from survey import bp_survey
from auth import bp_auth
from flask_cors import CORS
from dashboard import bp_dashboard
from assessment import bp_assessment
from datetime import timedelta



app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

CORS(app, supports_credentials=True)

# Подключение к базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:st53182@localhost/scrum_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)  # 🔄 Срок действия токена: 1 год
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=730)  # 🔄 Refresh-токен: 2 года

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "options": "-c timezone=utc"
    }
}

# JWT настройка
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
jwt = JWTManager(app)

# 🟢 Инициализация базы данных
db.init_app(app)

with app.app_context():  # Важно!
    db.create_all()  # Создаём таблицы, если их нет

# Регистрация маршрутов
app.register_blueprint(bp_auth)
app.register_blueprint(bp_survey)
app.register_blueprint(bp_dashboard, url_prefix="/dashboard")

app.register_blueprint(bp_assessment)




@app.route('/')
def home():
    return {"message": "Scrum Maturity App API is running!"}




if __name__ == '__main__':
    app.run(debug=True)


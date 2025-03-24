from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from database import db
from models import User
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import decode_token, get_jwt_identity
import jwt
import os
from models import User

bp_auth = Blueprint('auth', __name__)

@bp_auth.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"})

@bp_auth.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token})


SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token or "Bearer " not in token:
            return jsonify({"error": "Токен отсутствует!"}), 401

        token = token.split(" ")[1]  # Убираем "Bearer "

        try:
            data = decode_token(token)
            current_user = User.query.get(data["sub"])
            if not current_user:
                return jsonify({"error": "Пользователь не найден"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Токен истёк"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Недействительный токен"}), 401

        return f(current_user, *args, **kwargs)

    return decorated

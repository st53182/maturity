
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/user_profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({
        "username": user.username,
        "name": user.name or "",
        "position": user.position or "",
        "company": user.company or "",
        "personality_type": user.personality_type or ""
    })


@profile_bp.route('/update_profile', methods=['POST'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    data = request.get_json()

    # Обновление общих данных
    user.name = data.get("name", user.name)
    user.position = data.get("position", user.position)
    user.company = data.get("company", user.company)
    user.personality_type = data.get("personality_type", user.personality_type)
    user.username = data.get("email", user.username)

    # Обновление пароля (если передан)
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if old_password and new_password:
        if not user.check_password(old_password):
            return jsonify({"error": "Старый пароль неверен"}), 403
        user.set_password(new_password)

    db.session.commit()
    return jsonify({"message": "Профиль обновлен"})

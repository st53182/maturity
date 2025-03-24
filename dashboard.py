from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Team
from survey import bp_survey
from flask_cors import cross_origin
from auth import token_required
from flask_cors import CORS
from flask import Flask


bp_dashboard = Blueprint("dashboard", __name__)

@bp_dashboard.route("/delete_team/<int:team_id>", methods=["DELETE"])
@cross_origin()
@token_required
def delete_team(current_user, team_id):
    team = Team.query.filter_by(id=team_id, user_id=current_user.id).first()
    if not team:
        return jsonify({"error": "Команда не найдена или у вас нет прав на удаление"}), 404

    db.session.delete(team)
    db.session.commit()

    response = jsonify({"message": "Команда успешно удалена"})
    return response, 200


# ✅ planning_poker.py — полностью адаптирован под строковые room_id (например, UUID)

from flask import Blueprint, request, jsonify
from database import db
from models import PlanningRoom, Participant, Vote
from datetime import datetime
import uuid

planning_bp = Blueprint('planning_poker', __name__)

# Комната Planning Poker
@planning_bp.route('/planning-room', methods=['POST'])
def create_room():
    data = request.json
    room_id = str(uuid.uuid4())
    room = PlanningRoom(id=room_id, name=data['name'])
    db.session.add(room)
    db.session.commit()
    return jsonify({"room_id": room_id})

# Подключение к комнате
@planning_bp.route('/planning-room/<string:room_id>/join', methods=['POST', 'OPTIONS'])
def join_room(room_id):
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    participant = Participant(name=data['name'], role=data['role'], room_id=room_id)
    db.session.add(participant)
    db.session.commit()
    return jsonify({"participant_id": participant.id})

# Список участников комнаты
@planning_bp.route('/planning-room/<string:room_id>/participants', methods=['GET'])
def get_participants(room_id):
    participants = Participant.query.filter_by(room_id=room_id).all()
    votes = Vote.query.filter_by(room_id=room_id).all()
    vote_map = {vote.participant_id: vote.points for vote in votes}

    result = []
    for p in participants:
        result.append({
            "id": p.id,
            "name": p.name,
            "role": p.role,
            "voted": p.id in vote_map,
            "points": vote_map.get(p.id)
        })

    return jsonify({"participants": result})

# Голосование
@planning_bp.route('/planning-room/<string:room_id>/vote', methods=['POST'])
def vote(room_id):
    data = request.json
    vote = Vote(
        story=data['story'],
        points=data['points'],
        participant_id=data['participant_id'],
        room_id=room_id,
        created_at=datetime.utcnow()
    )
    db.session.add(vote)
    db.session.commit()
    return jsonify({"status": "ok"})

# Подсказки (по похожим оценкам)
@planning_bp.route('/planning-room/<string:room_id>/hints')
def get_hints(room_id):
    sp = request.args.get("sp")
    role = request.args.get("role")

    votes = Vote.query.join(Participant).filter(
        Vote.room_id == room_id,
        Vote.points == sp,
        Participant.role == role
    ).all()

    hints = [
        {"story": v.story, "points": v.points} for v in votes
    ]

    return jsonify({"hints": hints})

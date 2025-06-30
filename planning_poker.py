# planning_poker.py
from flask import Blueprint, request, jsonify
from database import db
from models import PlanningRoom, Participant, Vote

planning_bp = Blueprint('planning_poker', __name__)

@planning_bp.route('/planning-room', methods=['POST'])
def create_room():
    data = request.json
    room = PlanningRoom(name=data['name'])
    db.session.add(room)
    db.session.commit()
    return jsonify({"room_id": room.id})

@planning_bp.route('/planning-room/<int:room_id>/join', methods=['POST'])
def join_room(room_id):
    data = request.json
    participant = Participant(name=data['name'], role=data['role'], room_id=room_id)
    db.session.add(participant)
    db.session.commit()
    return jsonify({"participant_id": participant.id})

# и так далее: голосование, подсказки, история


@planning_bp.route('/planning-room/<int:room_id>/participants', methods=['GET'])
def get_participants(room_id):
    from models import Participant, Vote

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

# planning_poker.py
from flask import Blueprint, request, jsonify
from database import db_session
from models import PlanningRoom, Participant, Vote

planning_bp = Blueprint('planning_poker', __name__)

@planning_bp.route('/api/planning-room', methods=['POST'])
def create_room():
    data = request.json
    room = PlanningRoom(name=data['name'])
    db_session.add(room)
    db_session.commit()
    return jsonify({"room_id": room.id})

@planning_bp.route('/api/planning-room/<int:room_id>/join', methods=['POST'])
def join_room(room_id):
    data = request.json
    participant = Participant(name=data['name'], role=data['role'], room_id=room_id)
    db_session.add(participant)
    db_session.commit()
    return jsonify({"participant_id": participant.id})

# и так далее: голосование, подсказки, история

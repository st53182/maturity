from flask import Blueprint, request, jsonify
from database import db
from models import PlanningRoom, Participant, Vote
from datetime import datetime

planning_bp = Blueprint('planning_poker', __name__)

@planning_bp.route('/planning-room', methods=['POST'])
def create_room():
    data = request.json
    room_id = data.get("id")
    room = PlanningRoom(id=room_id, name=data['name'])
    db.session.add(room)
    db.session.commit()
    return jsonify({"room_id": room.id})

@planning_bp.route('/planning-room/<string:room_id>/join', methods=['POST'])
def join_room(room_id):
    try:
        data = request.json
        room = PlanningRoom.query.get(room_id)
        if not room:
            room = PlanningRoom(id=room_id, name="Новая комната", created_at=datetime.utcnow())
            db.session.add(room)
            db.session.commit()

        participant = Participant(name=data['name'], role=data['role'], room_id=room_id)
        db.session.add(participant)
        db.session.commit()
        return jsonify({"participant_id": participant.id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/planning-room/<string:room_id>/participants', methods=['GET'])
def get_participants(room_id):
    try:
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/planning-room/<string:room_id>/vote', methods=['POST'])
def vote(room_id):
    try:
        data = request.json
        # Проверяем есть ли уже голос этого участника по этой комнате и истории
        existing_vote = Vote.query.filter_by(
            participant_id=data['participant_id'],
            room_id=room_id,
            story=data['story']
        ).first()

        if existing_vote:
            existing_vote.points = data['points']
            existing_vote.created_at = datetime.utcnow()
        else:
            new_vote = Vote(
                story=data['story'],
                points=data['points'],
                participant_id=data['participant_id'],
                room_id=room_id,
                created_at=datetime.utcnow()
            )
            db.session.add(new_vote)

        db.session.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

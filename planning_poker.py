from flask import Blueprint, request, jsonify
from database import db
from models import PlanningRoom, Participant, Vote, PokerStory
from datetime import datetime
import threading

planning_bp = Blueprint('planning_poker', __name__)


# 🔹 Создание комнаты (без списка задач)
@planning_bp.route('/planning-room', methods=['POST'])
def create_room():
    data = request.json
    room_id = data.get("id")
    room = PlanningRoom(id=room_id, name=data['name'])
    db.session.add(room)
    db.session.commit()
    return jsonify({"room_id": room.id})


# 🔹 Добавить задачу в комнату
@planning_bp.route('/planning-room/<string:room_id>/add-story', methods=['POST'])
def add_story(room_id):
    try:
        data = request.json
        title = data.get('title')
        description = data.get('description', "")

        if not title:
            return jsonify({"error": "Заголовок задачи обязателен"}), 400

        story = PokerStory(
            room_id=room_id,
            title=title,
            description=description
        )
        db.session.add(story)
        db.session.commit()
        print(f"[ADD_STORY] Добавлена задача '{title}' в комнату {room_id}")

        return jsonify({
            "story_id": story.id,
            "title": story.title,
            "description": story.description
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 🔹 Получить все задачи комнаты
@planning_bp.route('/planning-room/<string:room_id>/stories', methods=['GET'])
def get_stories(room_id):
    stories = PokerStory.query.filter_by(room_id=room_id).all()
    result = [{
        "id": s.id,
        "title": s.title,
        "description": s.description
    } for s in stories]

    return jsonify({"stories": result})


# 🔹 Присоединение к комнате
@planning_bp.route('/planning-room/<string:room_id>/join', methods=['POST'])
def join_room(room_id):
    try:
        data = request.json
        participant = Participant.query.filter_by(
            name=data['name'],
            role=data['role'],
            room_id=room_id
        ).first()

        if participant:
            return jsonify({"participant_id": participant.id})

        participant = Participant(
            name=data['name'],
            role=data['role'],
            room_id=room_id
        )
        db.session.add(participant)
        db.session.commit()
        return jsonify({"participant_id": participant.id})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 🔹 Получить участников и флаг show_votes
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

    room = PlanningRoom.query.get(room_id)
    return jsonify({
        "participants": result,
        "show_votes": room.show_votes
    })


# 🔹 Отправка/обновление голоса
@planning_bp.route('/planning-room/<string:room_id>/vote', methods=['POST'])
def vote(room_id):
    try:
        data = request.json
        existing_vote = Vote.query.filter_by(
            participant_id=data['participant_id'],
            room_id=room_id,
            story_id=data['story_id']
        ).first()

        if existing_vote:
            existing_vote.points = data['points']
        else:
            new_vote = Vote(
                story_id=data['story_id'],
                story=data['story_title'],  # для совместимости
                points=data['points'],
                participant_id=data['participant_id'],
                room_id=room_id
            )
            db.session.add(new_vote)

        db.session.commit()
        return jsonify({"status": "ok"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 🔹 Вскрытие оценок через 3 секунды
@planning_bp.route('/planning-room/<string:room_id>/show-votes', methods=['POST'])
def show_votes(room_id):
    def delayed_show():
        room = PlanningRoom.query.get(room_id)
        room.show_votes = True
        db.session.commit()
        print(f"[SHOW_VOTES] Оценки вскрыты в комнате {room_id}")

    threading.Timer(3.0, delayed_show).start()
    return jsonify({"status": "votes_will_be_visible_in_3_sec"})


# 🔹 Подсказки по прошлым голосам
@planning_bp.route('/planning-room/<string:room_id>/hints', methods=['GET'])
def get_hints(room_id):
    role = request.args.get('role')
    sp = int(request.args.get('sp'))

    votes = Vote.query.join(Participant).filter(
        Vote.room_id == room_id,
        Participant.role == role,
        Vote.points == sp
    ).all()

    hints = [{
        "story": vote.story,
        "points": vote.points
    } for vote in votes]

    return jsonify({"hints": hints})
@planning_bp.route('/planning-room/<string:room_id>/leave/<int:participant_id>', methods=['POST'])
def leave_room(room_id, participant_id):
    try:
        participant = Participant.query.filter_by(id=participant_id, room_id=room_id).first()
        if not participant:
            return jsonify({"error": "Участник не найден"}), 404

        db.session.delete(participant)
        db.session.commit()
        print(f"[LEAVE_ROOM] Участник {participant_id} покинул комнату {room_id}")
        return jsonify({"status": "left"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
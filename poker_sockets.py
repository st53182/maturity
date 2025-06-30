from flask_socketio import emit, join_room, leave_room
from flask import request
from models import db, Participant, PokerSession, Estimate, Story
from app import socketio

@socketio.on("join_session")
def handle_join_session(data):
    session_id = data["session_id"]
    name = data["name"]
    role = data["role"]
    socket_id = request.sid

    participant = Participant(session_id=session_id, name=name, role=role, socket_id=socket_id)
    db.session.add(participant)
    db.session.commit()

    join_room(str(session_id))

    emit("user_joined", {"name": name, "role": role}, room=str(session_id))
    send_participant_list(session_id)


@socketio.on("submit_estimate")
def handle_submit_estimate(data):
    story_id = data["story_id"]
    session_id = data["session_id"]
    participant_id = data["participant_id"]
    value = data["value"]
    estimate_type = data["estimate_type"]

    estimate = Estimate(
        story_id=story_id,
        participant_id=participant_id,
        value=value,
        estimate_type=estimate_type
    )
    db.session.add(estimate)
    db.session.commit()

    emit("vote_submitted", {"participant_id": participant_id}, room=str(session_id))


@socketio.on("reveal_estimates")
def handle_reveal(data):
    story_id = data["story_id"]
    session_id = data["session_id"]
    estimates = Estimate.query.filter_by(story_id=story_id).all()
    for e in estimates:
        e.revealed = True
    db.session.commit()

    emit("estimates_revealed", {"story_id": story_id}, room=str(session_id))


def send_participant_list(session_id):
    participants = Participant.query.filter_by(session_id=session_id).all()
    emit("update_participants", [
        {"id": p.id, "name": p.name, "role": p.role} for p in participants
    ], room=str(session_id))

"""Личный чат по e-mail участника: REST + Socket.IO namespace /community (онлайн и push новых сообщений)."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Set

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError

from database import db
from models import ChatContact, DirectMessage, User
from flask_socketio import emit, join_room

bp_community_chat = Blueprint("community_chat", __name__, url_prefix="/api/chat")

socketio_ref = None

sid_to_user: Dict[str, int] = {}
user_sids: Dict[int, Set[str]] = defaultdict(set)
watchers: Dict[int, Set[int]] = defaultdict(set)
watcher_by_peer: Dict[int, Set[int]] = defaultdict(set)


def _user_room(uid: int) -> str:
    return f"u_{uid}"


def _notify_peer_presence_changed(peer_id: int, online: bool) -> None:
    if socketio_ref is None:
        return
    for wid in list(watcher_by_peer.get(peer_id, ())):
        socketio_ref.emit(
            "peer_presence",
            {"peer_id": peer_id, "online": online},
            room=_user_room(wid),
            namespace="/community",
        )


def _peer_online(peer_id: int) -> bool:
    return peer_id in user_sids and len(user_sids[peer_id]) > 0


def register_community_socketio_handlers(sio):
    global socketio_ref
    socketio_ref = sio

    @sio.on("connect", namespace="/community")
    def community_connect(auth):
        try:
            auth = auth or {}
            token = auth.get("token")
            if not token:
                return False
            decoded = decode_token(token)
            user_id = int(decoded["sub"])
            sid = request.sid
            sid_to_user[sid] = user_id
            user_sids[user_id].add(sid)
            if len(user_sids[user_id]) == 1:
                _notify_peer_presence_changed(user_id, True)
            join_room(_user_room(user_id), sid=sid, namespace="/community")
            return True
        except Exception as e:
            print(f"community connect error: {e}")
            return False

    @sio.on("disconnect", namespace="/community")
    def community_disconnect():
        sid = request.sid
        user_id = sid_to_user.pop(sid, None)
        if user_id is None:
            return
        user_sids[user_id].discard(sid)
        if not user_sids[user_id]:
            del user_sids[user_id]
            _notify_peer_presence_changed(user_id, False)
        for peer_id in list(watchers.pop(user_id, ())):
            watcher_by_peer[peer_id].discard(user_id)

    @sio.on("watch_presence", namespace="/community")
    def on_watch_presence(data):
        sid = request.sid
        uid = sid_to_user.get(sid)
        if not uid or not data:
            return
        try:
            peer_id = int(data.get("peer_id", 0))
        except (TypeError, ValueError):
            return
        if peer_id <= 0 or peer_id == uid:
            return
        if not User.query.get(peer_id):
            return
        watchers[uid].add(peer_id)
        watcher_by_peer[peer_id].add(uid)
        emit("peer_presence", {"peer_id": peer_id, "online": _peer_online(peer_id)})

    @sio.on("unwatch_presence", namespace="/community")
    def on_unwatch_presence(data):
        sid = request.sid
        uid = sid_to_user.get(sid)
        if not uid or not data:
            return
        try:
            peer_id = int(data.get("peer_id", 0))
        except (TypeError, ValueError):
            return
        watchers[uid].discard(peer_id)
        watcher_by_peer[peer_id].discard(uid)


def _message_payload(msg: DirectMessage) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "body": msg.body,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _ensure_single_contact(owner_id: int, contact_id: int) -> None:
    """Одна запись owner → contact; идемпотентно, с защитой от гонок."""
    if owner_id == contact_id:
        return
    if ChatContact.query.filter_by(user_id=owner_id, contact_user_id=contact_id).first():
        return
    db.session.add(ChatContact(user_id=owner_id, contact_user_id=contact_id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def _emit_contacts_changed(user_ids: list) -> None:
    if not socketio_ref:
        return
    for uid in user_ids:
        socketio_ref.emit(
            "chat_contacts_changed",
            {},
            room=_user_room(int(uid)),
            namespace="/community",
        )


@bp_community_chat.route("/presence", methods=["POST"])
@jwt_required()
def check_presence():
    """Bulk presence check — returns online status for a list of user IDs."""
    data = request.get_json() or {}
    ids = data.get("ids") or []
    if not isinstance(ids, list):
        return jsonify({"error": "bad_ids"}), 400
    result = {}
    for uid in ids[:50]:
        try:
            uid = int(uid)
        except (TypeError, ValueError):
            continue
        result[str(uid)] = _peer_online(uid)
    return jsonify({"presence": result}), 200


@bp_community_chat.route("/resolve", methods=["POST"])
@jwt_required()
def resolve_peer():
    me = int(get_jwt_identity())
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "invalid_email"}), 400
    peer = User.query.filter(func.lower(User.username) == email).first()
    if not peer:
        return jsonify({"found": False}), 200
    if peer.id == me:
        return jsonify({"found": False, "error": "self"}), 400
    _ensure_single_contact(me, peer.id)
    _ensure_single_contact(peer.id, me)
    _emit_contacts_changed([me, peer.id])
    return jsonify(
        {
            "found": True,
            "user": {
                "id": peer.id,
                "name": peer.name or "",
                "username": peer.username,
            },
        }
    ), 200


@bp_community_chat.route("/contacts", methods=["GET"])
@jwt_required()
def list_contacts():
    me = int(get_jwt_identity())
    rows = (
        db.session.query(ChatContact, User)
        .join(User, ChatContact.contact_user_id == User.id)
        .filter(ChatContact.user_id == me)
        .order_by(ChatContact.created_at.desc())
        .all()
    )
    out = [
        {
            "id": u.id,
            "name": u.name or "",
            "username": u.username,
            "added_at": cc.created_at.isoformat() if cc.created_at else None,
        }
        for cc, u in rows
    ]
    return jsonify({"contacts": out}), 200


@bp_community_chat.route("/contacts/<int:contact_user_id>", methods=["DELETE"])
@jwt_required()
def delete_contact(contact_user_id):
    me = int(get_jwt_identity())
    if contact_user_id == me:
        return jsonify({"error": "self"}), 400
    deleted = False
    for uid_a, uid_b in ((me, contact_user_id), (contact_user_id, me)):
        row = ChatContact.query.filter_by(user_id=uid_a, contact_user_id=uid_b).first()
        if row:
            db.session.delete(row)
            deleted = True
    if not deleted:
        return jsonify({"error": "not_found"}), 404
    db.session.commit()
    _emit_contacts_changed([me, contact_user_id])
    return jsonify({"ok": True}), 200


@bp_community_chat.route("/messages/<int:peer_id>", methods=["GET"])
@jwt_required()
def get_messages(peer_id):
    me = int(get_jwt_identity())
    if peer_id == me:
        return jsonify({"error": "self"}), 400
    peer = User.query.get(peer_id)
    if not peer:
        return jsonify({"error": "not_found"}), 404
    limit = min(max(int(request.args.get("limit", 80)), 1), 200)
    before_id = request.args.get("before_id", type=int)
    q = (
        DirectMessage.query.filter(
            or_(
                and_(DirectMessage.sender_id == me, DirectMessage.recipient_id == peer_id),
                and_(DirectMessage.sender_id == peer_id, DirectMessage.recipient_id == me),
            )
        )
        .order_by(DirectMessage.id.desc())
    )
    if before_id:
        q = q.filter(DirectMessage.id < before_id)
    rows = q.limit(limit).all()
    rows.reverse()
    out = []
    for m in rows:
        d = _message_payload(m)
        d["mine"] = m.sender_id == me
        out.append(d)
    return jsonify({"messages": out}), 200


@bp_community_chat.route("/send", methods=["POST"])
@jwt_required()
def send_message():
    me = int(get_jwt_identity())
    data = request.get_json() or {}
    try:
        recipient_id = int(data.get("recipient_id", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "bad_recipient"}), 400
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "empty"}), 400
    if len(body) > 8000:
        return jsonify({"error": "too_long"}), 400
    if recipient_id == me:
        return jsonify({"error": "self"}), 400
    peer = User.query.get(recipient_id)
    if not peer:
        return jsonify({"error": "not_found"}), 404
    msg = DirectMessage(sender_id=me, recipient_id=recipient_id, body=body)
    db.session.add(msg)
    db.session.commit()
    payload = _message_payload(msg)
    if socketio_ref:
        socketio_ref.emit("dm_new", payload, room=_user_room(recipient_id), namespace="/community")
        socketio_ref.emit("dm_new", payload, room=_user_room(me), namespace="/community")
    return jsonify({"message": payload}), 201

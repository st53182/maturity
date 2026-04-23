"""Три тренажёра продуктового мышления: User/Job stories, USM, Kanban-система.

API: /api/agile-training/ws/<exercise_key>/…
exercise_key: product_stories | user_story_map | kanban_system
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingKanbanSystemAnswer,
    AgileTrainingParticipant,
    AgileTrainingProductStoriesAnswer,
    AgileTrainingSession,
    AgileTrainingUserStoryMapAnswer,
)
from workshop_content import get_workshop_content

bp_agile_workshops = Blueprint("agile_workshops", __name__, url_prefix="/api/agile-training/ws")

_EXERCISE_TO_MODEL: Dict[str, Type[Any]] = {
    "product_stories": AgileTrainingProductStoriesAnswer,
    "user_story_map": AgileTrainingUserStoryMapAnswer,
    "kanban_system": AgileTrainingKanbanSystemAnswer,
}


def _uid() -> int:
    return int(get_jwt_identity())


def _safe_json(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        o = json.loads(raw)
        return o if isinstance(o, dict) else {}
    except Exception:
        return {}


def _resolve_locale(a: Optional[str], sess: Optional[AgileTrainingSession]) -> str:
    c = (a or "").strip().lower()[:4]
    if c in {"ru", "en"}:
        return c
    s = (getattr(sess, "locale", None) or "ru") if sess else "ru"
    return s if s in {"ru", "en"} else "ru"


def _group_by_slug(slug: str) -> Optional[AgileTrainingGroup]:
    return AgileTrainingGroup.query.filter_by(slug=(slug or "").strip()).first()


def _session_for_owner(sid: int, uid: int) -> Optional[AgileTrainingSession]:
    return AgileTrainingSession.query.filter_by(id=sid, owner_user_id=uid).first()


def _model_for(ex: str) -> Optional[Type[Any]]:
    return _EXERCISE_TO_MODEL.get(ex)


def _verify_session_group(g: AgileTrainingGroup, exercise_key: str) -> bool:
    sess = AgileTrainingSession.query.get(g.session_id)
    return bool(sess and getattr(sess, "exercise_key", None) == exercise_key)


# ---------------- public ----------------


@bp_agile_workshops.get("/<exercise_key>/content")
def public_content(exercise_key: str):
    if not _model_for(exercise_key):
        return jsonify({"error": "Unknown exercise"}), 404
    loc = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": loc, **get_workshop_content(exercise_key, loc)})


@bp_agile_workshops.get("/<exercise_key>/g/<slug>/state")
def participant_state(exercise_key: str, slug: str):
    m = _model_for(exercise_key)
    if not m:
        return jsonify({"error": "Unknown exercise"}), 404
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    if not _verify_session_group(g, exercise_key):
        return jsonify({"error": "This link is for a different exercise"}), 400
    sess = AgileTrainingSession.query.get(g.session_id)
    loc = _resolve_locale(request.args.get("locale"), sess)
    content = get_workshop_content(exercise_key, loc)

    token = (request.args.get("participant_token") or "").strip()
    data_out: Optional[Dict] = None
    if token:
        p = (
            AgileTrainingParticipant.query
            .filter_by(group_id=g.id, participant_token=token)
            .first()
        )
        if p:
            a = m.query.filter_by(participant_id=p.id).first()
            if a:
                data_out = _safe_json(a.data_json)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "exercise_key": exercise_key,
        "session_locale": getattr(sess, "locale", "ru") if sess else "ru",
        "effective_locale": loc,
        "content": content,
        "data": data_out,
    })


@bp_agile_workshops.post("/<exercise_key>/g/<slug>/save")
def participant_save(exercise_key: str, slug: str):
    m = _model_for(exercise_key)
    if not m:
        return jsonify({"error": "Unknown exercise"}), 404
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    if not _verify_session_group(g, exercise_key):
        return jsonify({"error": "This link is for a different exercise"}), 400

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id, participant_token=token)
        .first()
    )
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    payload = body.get("data")
    if not isinstance(payload, dict):
        return jsonify({"error": "data must be an object"}), 400
    if len(json.dumps(payload, ensure=False)) > 200_000:
        return jsonify({"error": "data too large"}), 400

    a = m.query.filter_by(participant_id=p.id).first()
    if not a:
        a = m(group_id=g.id, participant_id=p.id, data_json="{}")
        db.session.add(a)
    a.data_json = json.dumps(payload, ensure_ascii=False)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


# --------------- facilitator ---------------


@bp_agile_workshops.get("/<exercise_key>/groups/<int:group_id>/participants")
@jwt_required()
def fac_participants(exercise_key: str, group_id: int):
    m = _model_for(exercise_key)
    if not m:
        return jsonify({"error": "Unknown exercise"}), 404
    uid = _uid()
    grp = AgileTrainingGroup.query.get(group_id)
    if not grp:
        return jsonify({"error": "Group not found"}), 404
    sess = _session_for_owner(grp.session_id, uid)
    if not sess or sess.exercise_key != exercise_key:
        return jsonify({"error": "Forbidden"}), 403

    out = []
    for p in AgileTrainingParticipant.query.filter_by(group_id=group_id).all():
        a = m.query.filter_by(participant_id=p.id).first()
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "has_data": bool(a and _safe_json(a.data_json)),
            "data": _safe_json(a.data_json) if a else None,
            "updated_at": a.updated_at.isoformat() if a and a.updated_at else None,
        })
    return jsonify({"participants": out})


@bp_agile_workshops.post("/<exercise_key>/groups/<int:group_id>/reset")
@jwt_required()
def fac_reset(exercise_key: str, group_id: int):
    m = _model_for(exercise_key)
    if not m:
        return jsonify({"error": "Unknown exercise"}), 404
    uid = _uid()
    grp = AgileTrainingGroup.query.get(group_id)
    if not grp:
        return jsonify({"error": "Group not found"}), 404
    if not _session_for_owner(grp.session_id, uid):
        return jsonify({"error": "Forbidden"}), 403
    m.query.filter_by(group_id=group_id).delete()
    db.session.commit()
    return jsonify({"ok": True})


@bp_agile_workshops.get("/<exercise_key>/sessions/<int:session_id>/summary")
@jwt_required()
def fac_session_summary(exercise_key: str, session_id: int):
    m = _model_for(exercise_key)
    if not m:
        return jsonify({"error": "Unknown exercise"}), 404
    uid = _uid()
    sess = _session_for_owner(session_id, uid)
    if not sess or getattr(sess, "exercise_key", None) != exercise_key:
        return jsonify({"error": "Not found"}), 404
    groups_out = []
    for g in AgileTrainingGroup.query.filter_by(session_id=session_id).all():
        n = 0
        for p in g.participants:
            if m.query.filter_by(participant_id=p.id).first():
                n += 1
        groups_out.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants": g.participants.count(),
            "submitted": n,
        })
    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": getattr(sess, "locale", "ru")},
        "groups": groups_out,
    })

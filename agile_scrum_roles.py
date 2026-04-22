"""Backend тренажёра «Роли в Scrum».

API под префиксом `/api/agile-training/scrum-roles`.

Одна запись на участника (AgileTrainingScrumRolesAnswer). В data_json
лежит selection + evaluation + errors_seen + custom_cards + custom_role.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingScrumRolesAnswer,
    AgileTrainingSession,
)
from scrum_roles_content import (
    CARDS,
    ROLE_KEYS,
    card_title,
    evaluate_selection,
    get_content_for_locale,
    level_title,
    role_title,
    sanitize_custom_cards,
    sanitize_custom_role,
    sanitize_errors,
    sanitize_selection,
)


bp_agile_scrum_roles = Blueprint(
    "agile_scrum_roles", __name__, url_prefix="/api/agile-training/scrum-roles"
)


# --------------------------- helpers ---------------------------


def _uid() -> int:
    return int(get_jwt_identity())


def _resolve_locale(explicit: Optional[str], session: Optional[AgileTrainingSession]) -> str:
    lc = (explicit or "").strip().lower()
    if lc in {"ru", "en"}:
        return lc
    lc = (getattr(session, "locale", None) or "ru") if session else "ru"
    return lc if lc in {"ru", "en"} else "ru"


def _group_by_slug(slug: str) -> Optional[AgileTrainingGroup]:
    return AgileTrainingGroup.query.filter_by(slug=(slug or "").strip()).first()


def _session_for_owner(session_id: int, uid: int) -> Optional[AgileTrainingSession]:
    return AgileTrainingSession.query.filter_by(id=session_id, owner_user_id=uid).first()


def _safe_json_load(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


# --------------------------- public (participant) ---------------------------


@bp_agile_scrum_roles.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **get_content_for_locale(locale)})


@bp_agile_scrum_roles.get("/g/<slug>/state")
def participant_state(slug: str):
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)

    token = (request.args.get("participant_token") or "").strip()
    answer_payload: Optional[Dict] = None
    if token:
        p = (
            AgileTrainingParticipant.query
            .filter_by(group_id=g.id, participant_token=token)
            .first()
        )
        if p:
            a = (
                AgileTrainingScrumRolesAnswer.query
                .filter_by(participant_id=p.id)
                .first()
            )
            if a:
                answer_payload = {
                    "score": a.score,
                    "max_score": a.max_score,
                    "health_pct": a.health_pct,
                    "data": _safe_json_load(a.data_json),
                }

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "exercise_key": sess.exercise_key if sess else "scrum_roles",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "content": get_content_for_locale(locale),
        "answer": answer_payload,
    })


@bp_agile_scrum_roles.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """body:
      {
        "participant_token": "...",
        "selection": { card_key: { role_key: level|null } },
        "errors_seen": [...],
        "custom_cards": [{title, assigned}],
        "custom_role": {title, desc}
      }
    """
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

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

    clean_selection = sanitize_selection(body.get("selection"))
    evaluation = evaluate_selection(clean_selection)
    errors_seen = sanitize_errors(body.get("errors_seen"))
    custom_cards = sanitize_custom_cards(body.get("custom_cards"))
    custom_role = sanitize_custom_role(body.get("custom_role"))

    a = (
        AgileTrainingScrumRolesAnswer.query
        .filter_by(participant_id=p.id)
        .first()
    )
    if not a:
        a = AgileTrainingScrumRolesAnswer(
            group_id=g.id,
            participant_id=p.id,
            data_json="{}",
        )
        db.session.add(a)

    payload = {
        "selection": clean_selection,
        "evaluation": evaluation,
        "errors_seen": errors_seen,
        "custom_cards": custom_cards,
        "custom_role": custom_role,
    }
    a.data_json = json.dumps(payload, ensure_ascii=False)
    a.score = int(evaluation["total"]["score"])
    a.max_score = int(evaluation["total"]["max"])
    a.health_pct = int(evaluation["total"]["health_pct"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "saved": True,
        "score": a.score,
        "max_score": a.max_score,
        "health_pct": a.health_pct,
        "evaluation": evaluation,
        "errors_seen": errors_seen,
        "custom_cards": custom_cards,
        "custom_role": custom_role,
    })


# ---- Агрегация ----


def _aggregate_group(group_id: int, locale: str) -> Dict:
    """За каждый (card, role) — сколько поставили каждый уровень.
    + health среднее, счётчики ошибок, кастомные карточки/роли."""
    rows = AgileTrainingScrumRolesAnswer.query.filter_by(group_id=group_id).all()
    participants = len(rows)
    if not participants:
        return {
            "participants_count": 0,
            "avg_health_pct": 0,
            "cards": [],
            "errors_seen": [],
            "custom_cards": [],
            "custom_roles": [],
            "color_totals": {"green": 0, "yellow": 0, "red": 0, "missing": 0},
        }

    total_health = 0
    # counts[card_key][role_key][level] = count
    counts: Dict[str, Dict[str, Dict[str, int]]] = {
        c["key"]: {rk: defaultdict(int) for rk in ROLE_KEYS} for c in CARDS
    }
    color_counts_per_cell: Dict[str, Dict[str, Dict[str, int]]] = {
        c["key"]: {rk: defaultdict(int) for rk in ROLE_KEYS} for c in CARDS
    }
    color_totals = {"green": 0, "yellow": 0, "red": 0, "missing": 0}
    errors_counter: Dict[str, int] = defaultdict(int)
    customs: List[Dict] = []
    custom_roles: List[Dict] = []

    for r in rows:
        total_health += int(r.health_pct or 0)
        data = _safe_json_load(r.data_json)
        selection = data.get("selection") or {}
        evaluation = (data.get("evaluation") or {}).get("cards") or {}
        for ck in counts.keys():
            for rk in ROLE_KEYS:
                picked = (selection.get(ck) or {}).get(rk)
                counts[ck][rk][picked or "none"] += 1
                col = ((evaluation.get(ck) or {}).get("roles") or {}).get(rk, {}).get("color")
                if col:
                    color_counts_per_cell[ck][rk][col] += 1
                    color_totals[col] = color_totals.get(col, 0) + 1
        for err in (data.get("errors_seen") or []):
            errors_counter[err] += 1
        for cc in (data.get("custom_cards") or []):
            customs.append(cc)
        cr = data.get("custom_role")
        if cr:
            custom_roles.append(cr)

    cards_view = []
    for c in CARDS:
        ck = c["key"]
        role_view = {}
        for rk in ROLE_KEYS:
            level_map = counts[ck][rk]
            items = []
            for lk in ["responsible", "participates", "should_not", "none"]:
                cnt = level_map.get(lk, 0)
                if cnt == 0:
                    continue
                items.append({
                    "level": lk if lk != "none" else None,
                    "level_title": level_title(lk, locale) if lk != "none" else "",
                    "count": cnt,
                    "pct": round(cnt / participants * 100),
                })
            role_view[rk] = {
                "levels": items,
                "colors": dict(color_counts_per_cell[ck][rk]),
            }
        cards_view.append({
            "key": ck,
            "title": card_title(ck, locale),
            "roles": role_view,
        })

    errors_view = [
        {"key": k, "count": v, "pct": round(v / participants * 100)}
        for k, v in sorted(errors_counter.items(), key=lambda x: -x[1])
    ]

    return {
        "participants_count": participants,
        "avg_health_pct": round(total_health / participants),
        "cards": cards_view,
        "errors_seen": errors_view,
        "custom_cards": customs[:20],
        "custom_roles": custom_roles[:20],
        "color_totals": color_totals,
    }


@bp_agile_scrum_roles.get("/g/<slug>/results")
def participant_results(slug: str):
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        **_aggregate_group(g.id, locale),
    })


# --------------------------- facilitator ---------------------------


@bp_agile_scrum_roles.get("/sessions/<int:session_id>/results")
@jwt_required()
def session_results(session_id: int):
    uid = _uid()
    sess = _session_for_owner(session_id, uid)
    if not sess:
        return jsonify({"error": "Session not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)

    groups = AgileTrainingGroup.query.filter_by(session_id=session_id).all()
    out = []
    total_participants = 0
    total_health = 0
    groups_with_answers = 0
    for g in groups:
        agg = _aggregate_group(g.id, locale)
        total_participants += agg["participants_count"]
        if agg["participants_count"]:
            total_health += agg["avg_health_pct"]
            groups_with_answers += 1
        out.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            **agg,
        })

    leaderboard = sorted(
        [g for g in out if g["participants_count"]],
        key=lambda x: (-x["avg_health_pct"], x["id"]),
    )

    return jsonify({
        "session": {
            "id": sess.id,
            "title": sess.title,
            "locale": sess.locale,
            "exercise_key": sess.exercise_key,
        },
        "groups": out,
        "totals": {
            "participants": total_participants,
            "avg_health_pct": round(total_health / groups_with_answers) if groups_with_answers else 0,
            "groups_with_answers": groups_with_answers,
            "groups_total": len(groups),
        },
        "leaderboard": leaderboard,
    })


@bp_agile_scrum_roles.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    uid = _uid()
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = _session_for_owner(g.session_id, uid)
    if not sess:
        return jsonify({"error": "Forbidden"}), 403
    locale = _resolve_locale(request.args.get("locale"), sess)
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        **_aggregate_group(g.id, locale),
    })


@bp_agile_scrum_roles.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    uid = _uid()
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = _session_for_owner(g.session_id, uid)
    if not sess:
        return jsonify({"error": "Forbidden"}), 403
    locale = _resolve_locale(request.args.get("locale"), sess)

    participants = AgileTrainingParticipant.query.filter_by(group_id=group_id).all()
    out = []
    for p in participants:
        a = (
            AgileTrainingScrumRolesAnswer.query
            .filter_by(participant_id=p.id)
            .first()
        )
        if not a:
            out.append({
                "id": p.id,
                "display_name": p.display_name,
                "has_answer": False,
            })
            continue
        data = _safe_json_load(a.data_json)
        selection = data.get("selection") or {}
        evaluation = (data.get("evaluation") or {}).get("cards") or {}
        cards_view = []
        for c in CARDS:
            ck = c["key"]
            ev_roles = (evaluation.get(ck) or {}).get("roles") or {}
            sel_roles = selection.get(ck) or {}
            role_view: Dict[str, Dict] = {}
            for rk in ROLE_KEYS:
                picked = sel_roles.get(rk)
                expected = (ev_roles.get(rk) or {}).get("expected")
                color = (ev_roles.get(rk) or {}).get("color")
                role_view[rk] = {
                    "picked": picked,
                    "picked_title": level_title(picked, locale) if picked else "",
                    "expected": expected,
                    "expected_title": level_title(expected, locale) if expected else "",
                    "color": color,
                }
            cards_view.append({
                "key": ck,
                "title": card_title(ck, locale),
                "color": (evaluation.get(ck) or {}).get("color"),
                "roles": role_view,
            })
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "has_answer": True,
            "score": a.score,
            "max_score": a.max_score,
            "health_pct": a.health_pct,
            "cards": cards_view,
            "errors_seen": data.get("errors_seen") or [],
            "custom_cards": data.get("custom_cards") or [],
            "custom_role": data.get("custom_role") or None,
        })
    return jsonify({"participants": out})


@bp_agile_scrum_roles.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    uid = _uid()
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = _session_for_owner(g.session_id, uid)
    if not sess:
        return jsonify({"error": "Forbidden"}), 403

    (
        AgileTrainingScrumRolesAnswer.query
        .filter_by(group_id=group_id)
        .delete()
    )
    db.session.commit()
    return jsonify({"ok": True})

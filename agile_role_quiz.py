"""Backend тренажёра «Кто отвечает?» (RACI-квиз по ситуациям).

API под префиксом `/api/agile-training/role-quiz`.

Одна запись на участника (AgileTrainingRoleQuizAnswer). В `data_json` лежит:
  - selection[situation_key][role_key] = 'accountable' | 'responsible' |
                                          'consulted' | 'informed' | 'not_involved' | null
  - evaluation: подробная разбивка по эталону
  - notes_seen: какие «типовые ошибки» / расшифровки участник уже посмотрел
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List, Optional, Set

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingRoleQuizAnswer,
    AgileTrainingSession,
)
from role_quiz_content import (
    LEVEL_KEYS,
    ROLE_KEYS,
    SITUATIONS,
    evaluate_selection,
    get_content_for_locale,
    level_title,
    role_title,
    sanitize_selection,
    situation_title,
    valid_situation_keys,
)


bp_agile_role_quiz = Blueprint(
    "agile_role_quiz", __name__, url_prefix="/api/agile-training/role-quiz"
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


def _sanitize_notes_seen(raw) -> List[str]:
    """Какие ситуации участник «раскрыл» (увидел rationale + common_mistake)."""
    if not isinstance(raw, list):
        return []
    valid = valid_situation_keys()
    seen: Set[str] = set()
    out: List[str] = []
    for k in raw:
        if isinstance(k, str) and k in valid and k not in seen:
            seen.add(k)
            out.append(k)
    return out


# --------------------------- public (participant) ---------------------------


@bp_agile_role_quiz.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **get_content_for_locale(locale)})


@bp_agile_role_quiz.get("/g/<slug>/state")
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
                AgileTrainingRoleQuizAnswer.query
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
        "exercise_key": sess.exercise_key if sess else "role_quiz",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "content": get_content_for_locale(locale),
        "answer": answer_payload,
    })


@bp_agile_role_quiz.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """body:
      {
        "participant_token": "...",
        "selection": { situation_key: { role_key: level|null } },
        "notes_seen": [...]
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
    notes_seen = _sanitize_notes_seen(body.get("notes_seen"))

    a = (
        AgileTrainingRoleQuizAnswer.query
        .filter_by(participant_id=p.id)
        .first()
    )
    if not a:
        a = AgileTrainingRoleQuizAnswer(
            group_id=g.id,
            participant_id=p.id,
            data_json="{}",
        )
        db.session.add(a)

    payload = {
        "selection": clean_selection,
        "evaluation": evaluation,
        "notes_seen": notes_seen,
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
        "notes_seen": notes_seen,
    })


# --------------------------- aggregation ---------------------------


def _aggregate_group(group_id: int, locale: str) -> Dict:
    rows = AgileTrainingRoleQuizAnswer.query.filter_by(group_id=group_id).all()
    participants = len(rows)
    if not participants:
        return {
            "participants_count": 0,
            "avg_health_pct": 0,
            "avg_accountable_correct": 0,
            "situations": [],
            "color_totals": {"green": 0, "yellow": 0, "red": 0, "missing": 0},
            "weak_situations": [],
        }

    total_health = 0
    total_acc_correct = 0
    counts: Dict[str, Dict[str, Dict[str, int]]] = {
        s["key"]: {rk: defaultdict(int) for rk in ROLE_KEYS} for s in SITUATIONS
    }
    color_counts_per_cell: Dict[str, Dict[str, Dict[str, int]]] = {
        s["key"]: {rk: defaultdict(int) for rk in ROLE_KEYS} for s in SITUATIONS
    }
    color_totals = {"green": 0, "yellow": 0, "red": 0, "missing": 0}
    situation_color_counts: Dict[str, Dict[str, int]] = {
        s["key"]: defaultdict(int) for s in SITUATIONS
    }

    for r in rows:
        total_health += int(r.health_pct or 0)
        data = _safe_json_load(r.data_json)
        evaluation = data.get("evaluation") or {}
        total_acc_correct += int(evaluation.get("accountable_correct") or 0)
        selection = data.get("selection") or {}
        sit_eval = evaluation.get("situations") or {}
        for sk in counts.keys():
            sit_color = (sit_eval.get(sk) or {}).get("color")
            if sit_color:
                situation_color_counts[sk][sit_color] += 1
            for rk in ROLE_KEYS:
                picked = (selection.get(sk) or {}).get(rk)
                counts[sk][rk][picked or "none"] += 1
                col = ((sit_eval.get(sk) or {}).get("roles") or {}).get(rk, {}).get("color")
                if col:
                    color_counts_per_cell[sk][rk][col] += 1
                    color_totals[col] = color_totals.get(col, 0) + 1

    situations_view = []
    for s in SITUATIONS:
        sk = s["key"]
        role_view = {}
        for rk in ROLE_KEYS:
            level_map = counts[sk][rk]
            items = []
            for lk in [*LEVEL_KEYS, "none"]:
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
                "colors": dict(color_counts_per_cell[sk][rk]),
            }
        sit_color_map = dict(situation_color_counts[sk])
        red_pct = round((sit_color_map.get("red", 0) / participants) * 100)
        situations_view.append({
            "key": sk,
            "title": situation_title(sk, locale),
            "roles": role_view,
            "color_counts": sit_color_map,
            "red_pct": red_pct,
        })

    weak_situations = sorted(
        situations_view, key=lambda x: -x["red_pct"]
    )[:5]

    return {
        "participants_count": participants,
        "avg_health_pct": round(total_health / participants),
        "avg_accountable_correct": round(total_acc_correct / participants, 1),
        "situations": situations_view,
        "color_totals": color_totals,
        "weak_situations": [
            {"key": w["key"], "title": w["title"], "red_pct": w["red_pct"]}
            for w in weak_situations if w["red_pct"] > 0
        ],
    }


@bp_agile_role_quiz.get("/g/<slug>/results")
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


@bp_agile_role_quiz.get("/sessions/<int:session_id>/results")
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


@bp_agile_role_quiz.get("/groups/<int:group_id>/results")
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


@bp_agile_role_quiz.get("/groups/<int:group_id>/participants")
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
            AgileTrainingRoleQuizAnswer.query
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
        evaluation = (data.get("evaluation") or {}).get("situations") or {}
        situations_view = []
        for s in SITUATIONS:
            sk = s["key"]
            ev_roles = (evaluation.get(sk) or {}).get("roles") or {}
            sel_roles = selection.get(sk) or {}
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
            situations_view.append({
                "key": sk,
                "title": situation_title(sk, locale),
                "color": (evaluation.get(sk) or {}).get("color"),
                "roles": role_view,
            })
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "has_answer": True,
            "score": a.score,
            "max_score": a.max_score,
            "health_pct": a.health_pct,
            "situations": situations_view,
            "notes_seen": data.get("notes_seen") or [],
        })
    return jsonify({"participants": out})


@bp_agile_role_quiz.post("/groups/<int:group_id>/reset")
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
        AgileTrainingRoleQuizAnswer.query
        .filter_by(group_id=group_id)
        .delete()
    )
    db.session.commit()
    return jsonify({"ok": True})

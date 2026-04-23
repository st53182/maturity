"""Backend тренажёра приоритизации WSJF.

API под префиксом `/api/agile-training/wsjf`.

Использует общие сущности обучающего каркаса
(AgileTrainingSession / Group / Participant) и хранит один ответ на
участника в `AgileTrainingWsjfAnswer`.
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
    AgileTrainingSession,
    AgileTrainingWsjfAnswer,
)
from wsjf_content import (
    EVENTS,
    OPTIONS,
    ROLES,
    analyze_adaptation,
    evaluate_round,
    get_content_for_locale,
    normalize_score_block,
    pick_event_for_choice,
    sanitize_round,
    simulate_outcome,
    valid_event_keys,
    valid_option_keys,
    valid_role_keys,
)


bp_agile_wsjf = Blueprint("agile_wsjf", __name__, url_prefix="/api/agile-training/wsjf")


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


def _load_json(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _event_by_key(key: Optional[str]) -> Optional[Dict]:
    if not key:
        return None
    for e in EVENTS:
        if e["key"] == key:
            return e
    return None


def _event_for_response(key: Optional[str], locale: str) -> Optional[Dict]:
    """Одно событие для API: `title` и `lead` — строки на выбранном языке, не {ru,en}."""
    raw = _event_by_key(key)
    if not raw:
        return None
    loc = "en" if (locale or "ru").strip().lower() == "en" else "ru"
    return {
        "key": raw["key"],
        "title": raw["title"][loc],
        "lead": raw["lead"][loc],
        "shifts": [dict(s) for s in raw["shifts"]],
        "favors": raw["favors"],
    }


def _recompute_adaptation(a: AgileTrainingWsjfAnswer) -> None:
    event = _event_by_key(a.event_key)
    adaptation = analyze_adaptation(a.initial_choice, a.revised_choice, event)
    a.adaptation = adaptation["status"]


# --------------------------- public (participant) ---------------------------


@bp_agile_wsjf.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **get_content_for_locale(locale)})


@bp_agile_wsjf.get("/g/<slug>/state")
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
            a = AgileTrainingWsjfAnswer.query.filter_by(participant_id=p.id).first()
            if a:
                answer_payload = {
                    "role_key": a.role_key,
                    "event_key": a.event_key,
                    "initial_choice": a.initial_choice,
                    "revised_choice": a.revised_choice,
                    "adaptation": a.adaptation,
                    "data": _load_json(a.data_json),
                }

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "exercise_key": sess.exercise_key if sess else "wsjf",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "content": get_content_for_locale(locale),
        "answer": answer_payload,
    })


@bp_agile_wsjf.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет раунд участника.

    body:
      {
        "participant_token": "...",
        "role_key": "business" | "engineer" | "strategist",
        "round": "initial" | "revised",
        "scores": { option_key: { value, time, risk, size } },
        "choice": option_key | null
      }
    Для raсчёта: WSJF считается на сервере, ошибки тоже.
    """
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    sess = AgileTrainingSession.query.get(g.session_id)
    body = request.get_json(silent=True) or {}
    request_locale = _resolve_locale(body.get("locale"), sess)
    token = (body.get("participant_token") or "").strip()
    role_key = (body.get("role_key") or "").strip()
    round_key = body.get("round") or "initial"
    if round_key not in {"initial", "revised"}:
        round_key = "initial"

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if role_key not in valid_role_keys():
        return jsonify({"error": "unknown role_key"}), 400

    p = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id, participant_token=token)
        .first()
    )
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    clean = sanitize_round(body)
    evaluation = evaluate_round(role_key, body)

    a = AgileTrainingWsjfAnswer.query.filter_by(participant_id=p.id).first()
    if not a:
        a = AgileTrainingWsjfAnswer(
            group_id=g.id,
            participant_id=p.id,
            role_key=role_key,
            data_json=json.dumps({}, ensure_ascii=False),
        )
        db.session.add(a)

    if round_key == "initial":
        a.role_key = role_key
        a.initial_choice = clean["choice"]
        a.revised_choice = None
        a.adaptation = None
        # выбираем событие под первый выбор участника
        event = pick_event_for_choice(clean["choice"])
        a.event_key = event["key"]
    elif a.role_key != role_key:
        return jsonify({"error": "role_key mismatch for revised round"}), 400
    else:
        a.revised_choice = clean["choice"]

    data = _load_json(a.data_json)
    if round_key == "initial":
        data["initial"] = {
            "scores": clean["scores"],
            "choice": clean["choice"],
            "eval": evaluation,
        }
        data["revised"] = None
        data["event_key"] = a.event_key
    else:
        data["revised"] = {
            "scores": clean["scores"],
            "choice": clean["choice"],
            "eval": evaluation,
        }
    a.data_json = json.dumps(data, ensure_ascii=False)
    _recompute_adaptation(a)
    db.session.commit()

    outcome = simulate_outcome(clean["choice"])

    resp = {
        "saved": True,
        "round": round_key,
        "eval": evaluation,
        "consequences": outcome,
        "initial_choice": a.initial_choice,
        "revised_choice": a.revised_choice,
        "event_key": a.event_key,
        "adaptation": a.adaptation,
    }
    if round_key == "initial" and a.event_key:
        resp["event"] = _event_for_response(a.event_key, request_locale)
    return jsonify(resp)


@bp_agile_wsjf.get("/g/<slug>/results")
def participant_results(slug: str):
    """Агрегация для финального экрана участника."""
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)

    rows = AgileTrainingWsjfAnswer.query.filter_by(group_id=g.id).all()
    total = len(rows)
    if not total:
        return jsonify({
            "group": {"id": g.id, "name": g.name, "slug": g.slug},
            "total_participants": g.participants.count(),
            "total_answers": 0,
            "initial_counts": {},
            "revised_counts": {},
            "adaptation_counts": {},
            "by_role": [],
        })

    init_cnt: Dict[str, int] = defaultdict(int)
    rev_cnt: Dict[str, int] = defaultdict(int)
    adapt_cnt: Dict[str, int] = defaultdict(int)
    by_role: Dict[str, Dict] = defaultdict(lambda: {
        "participants": 0,
        "choices": defaultdict(int),
    })
    for r in rows:
        if r.initial_choice:
            init_cnt[r.initial_choice] += 1
        if r.revised_choice:
            rev_cnt[r.revised_choice] += 1
        if r.adaptation:
            adapt_cnt[r.adaptation] += 1
        role = by_role[r.role_key]
        role["participants"] += 1
        k = r.revised_choice or r.initial_choice
        if k:
            role["choices"][k] += 1

    content = get_content_for_locale(locale)
    role_titles = {r["key"]: r["title"] for r in content["roles"]}
    by_role_view = []
    for role_key, d in by_role.items():
        by_role_view.append({
            "role_key": role_key,
            "role_title": role_titles.get(role_key, role_key),
            "participants": d["participants"],
            "choices": dict(d["choices"]),
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "total_participants": g.participants.count(),
        "total_answers": total,
        "initial_counts": dict(init_cnt),
        "revised_counts": dict(rev_cnt),
        "adaptation_counts": dict(adapt_cnt),
        "by_role": by_role_view,
    })


# --------------------------- facilitator ---------------------------


@bp_agile_wsjf.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    uid = _uid()
    sess = _session_for_owner(session_id, uid)
    if not sess:
        return jsonify({"error": "Not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), sess)
    content = get_content_for_locale(locale)

    groups = sess.groups.order_by(AgileTrainingGroup.id.asc()).all()
    groups_view = []
    totals = {"groups": 0, "participants": 0, "answers": 0}
    for g in groups:
        rows = AgileTrainingWsjfAnswer.query.filter_by(group_id=g.id).all()
        participants_count = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants_count
        totals["answers"] += len(rows)

        init_cnt: Dict[str, int] = defaultdict(int)
        rev_cnt: Dict[str, int] = defaultdict(int)
        adapt_cnt: Dict[str, int] = defaultdict(int)
        changed_count = 0
        for r in rows:
            if r.initial_choice:
                init_cnt[r.initial_choice] += 1
            if r.revised_choice:
                rev_cnt[r.revised_choice] += 1
            if r.adaptation:
                adapt_cnt[r.adaptation] += 1
            if r.initial_choice and r.revised_choice and r.initial_choice != r.revised_choice:
                changed_count += 1

        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants_count,
            "answers_count": len(rows),
            "initial_counts": dict(init_cnt),
            "revised_counts": dict(rev_cnt),
            "adaptation_counts": dict(adapt_cnt),
            "changed_mind_count": changed_count,
        })

    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "content": content,
        "totals": totals,
        "groups": groups_view,
    })


@bp_agile_wsjf.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)
    content = get_content_for_locale(locale)
    options_index = {o["key"]: o for o in content["options"]}
    roles_index = {r["key"]: r for r in content["roles"]}

    rows = AgileTrainingWsjfAnswer.query.filter_by(group_id=g.id).all()

    init_cnt: Dict[str, int] = defaultdict(int)
    rev_cnt: Dict[str, int] = defaultdict(int)
    adapt_cnt: Dict[str, int] = defaultdict(int)
    event_cnt: Dict[str, int] = defaultdict(int)
    error_cnt: Dict[str, int] = defaultdict(int)
    by_role: Dict[str, Dict] = defaultdict(lambda: {
        "participants": 0,
        "initial": defaultdict(int),
        "revised": defaultdict(int),
    })
    avg_scores: Dict[str, Dict[str, List[int]]] = defaultdict(
        lambda: {"value": [], "time": [], "risk": [], "size": []}
    )
    for r in rows:
        if r.initial_choice:
            init_cnt[r.initial_choice] += 1
        if r.revised_choice:
            rev_cnt[r.revised_choice] += 1
        if r.adaptation:
            adapt_cnt[r.adaptation] += 1
        if r.event_key:
            event_cnt[r.event_key] += 1
        payload = _load_json(r.data_json)
        eval_rd = (payload.get("revised") or payload.get("initial") or {}).get("eval", {}) or {}
        for er in eval_rd.get("errors") or []:
            error_cnt[er] += 1
        role = by_role[r.role_key]
        role["participants"] += 1
        if r.initial_choice:
            role["initial"][r.initial_choice] += 1
        if r.revised_choice:
            role["revised"][r.revised_choice] += 1
        source = payload.get("revised") or payload.get("initial") or {}
        for opt_key, block in (source.get("scores") or {}).items():
            if isinstance(block, dict):
                nb = normalize_score_block(block)
                for dim in ("value", "time", "risk", "size"):
                    v = nb.get(dim)
                    if isinstance(v, (int, float)):
                        avg_scores[opt_key][dim].append(int(v))

    avg_view = []
    for o in content["options"]:
        blk = avg_scores.get(o["key"], {"value": [], "time": [], "risk": [], "size": []})
        def _avg(arr):
            return round(sum(arr) / len(arr), 1) if arr else 0.0
        avg_view.append({
            "key": o["key"],
            "title": o["title"],
            "expected_scores": o["expected_scores"],
            "avg_value": _avg(blk["value"]),
            "avg_time": _avg(blk["time"]),
            "avg_risk": _avg(blk["risk"]),
            "avg_size": _avg(blk["size"]),
            "initial_pct": round(100 * init_cnt.get(o["key"], 0) / len(rows)) if rows else 0,
            "revised_pct": round(100 * rev_cnt.get(o["key"], 0) / len(rows)) if rows else 0,
        })

    by_role_view = []
    for rk, d in by_role.items():
        by_role_view.append({
            "role_key": rk,
            "role_title": roles_index.get(rk, {}).get("title", rk),
            "participants": d["participants"],
            "initial": dict(d["initial"]),
            "revised": dict(d["revised"]),
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "options": avg_view,
        "initial_counts": dict(init_cnt),
        "revised_counts": dict(rev_cnt),
        "adaptation_counts": dict(adapt_cnt),
        "event_counts": dict(event_cnt),
        "error_counts": dict(error_cnt),
        "by_role": by_role_view,
    })


@bp_agile_wsjf.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детали по каждому участнику: роль, выбор, scores, ошибки."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)
    content = get_content_for_locale(locale)
    options_index = {o["key"]: o for o in content["options"]}
    roles_index = {r["key"]: r for r in content["roles"]}
    events_index = {e["key"]: e for e in content["events"]}

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows_out = []
    for idx, p in enumerate(participants, start=1):
        a = AgileTrainingWsjfAnswer.query.filter_by(participant_id=p.id).first()
        if not a:
            rows_out.append({
                "id": p.id,
                "display_name": p.display_name or f"#{idx}",
                "anonymous_label": f"#{idx}",
                "joined_at": p.created_at.isoformat() if p.created_at else None,
                "has_answer": False,
            })
            continue
        payload = _load_json(a.data_json)

        def _opt(key: Optional[str]):
            if not key:
                return None
            o = options_index.get(key)
            return {"key": key, "title": o["title"] if o else key}

        def _hydrate(side: Optional[Dict]):
            if not side:
                return None
            scores = []
            for opt_key, block in (side.get("scores") or {}).items():
                o = options_index.get(opt_key)
                wsjf = (side.get("eval") or {}).get("wsjf", {}).get(opt_key)
                nb = normalize_score_block(block) if isinstance(block, dict) else {}
                scores.append({
                    "key": opt_key,
                    "title": o["title"] if o else opt_key,
                    "value": nb.get("value"),
                    "time": nb.get("time"),
                    "risk": nb.get("risk"),
                    "size": nb.get("size"),
                    "wsjf": wsjf,
                })
            return {
                "choice": _opt(side.get("choice")),
                "scores": scores,
                "eval": side.get("eval"),
            }

        rows_out.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "has_answer": True,
            "role_key": a.role_key,
            "role_title": roles_index.get(a.role_key, {}).get("title", a.role_key),
            "event": events_index.get(a.event_key) if a.event_key else None,
            "initial_choice": _opt(a.initial_choice),
            "revised_choice": _opt(a.revised_choice),
            "adaptation": a.adaptation,
            "initial": _hydrate(payload.get("initial")),
            "revised": _hydrate(payload.get("revised")),
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows_out,
    })


@bp_agile_wsjf.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404
    AgileTrainingWsjfAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})

"""Backend тренажёра «Ритм работы команды» (Scrum events).

API под префиксом `/api/agile-training/scrum-events`.

Сценарий: участник собирает 4 события (Planning, Daily, Review, Retro) из
атомарных карточек (goals/participants/artifacts/time/duration). Эталон для
дебрифа отдаётся только фасилитатору (JWT); в ответе state/content для
участника поле reference не передаётся.

Одна запись на участника (AgileTrainingScrumEventsAnswer). В data_json
лежит selection + evaluation + список ошибок, с которыми сталкивался +
кастомный режим (если собран)."""

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
    AgileTrainingScrumEventsAnswer,
    AgileTrainingSession,
)
from scrum_events_content import (
    CATEGORIES,
    STAGE_KEYS,
    card_title,
    evaluate_selection,
    get_content_for_participant,
    get_facilitator_reference_view,
    get_content_for_locale,
    sanitize_selection,
    stage_title,
    valid_card_keys,
    valid_custom_keys,
    valid_error_keys,
    valid_stage_keys,
)


bp_agile_scrum_events = Blueprint(
    "agile_scrum_events", __name__, url_prefix="/api/agile-training/scrum-events"
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


def _sanitize_errors(raw) -> List[str]:
    if not isinstance(raw, list):
        return []
    valid = valid_error_keys()
    out: List[str] = []
    seen = set()
    for k in raw:
        if isinstance(k, str) and k in valid and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _sanitize_custom(raw) -> Optional[Dict]:
    if not isinstance(raw, dict):
        return None
    ctx = (raw.get("context_key") or "").strip()
    if ctx and ctx not in valid_custom_keys():
        ctx = ""
    selection = raw.get("selection") or {}
    clean_sel: Dict[str, List[str]] = {}
    if isinstance(selection, dict):
        for cat in CATEGORIES:
            arr = selection.get(cat) or []
            if not isinstance(arr, list):
                arr = []
            valid = valid_card_keys(cat)
            seen = set()
            clean: List[str] = []
            for k in arr:
                if isinstance(k, str) and k in valid and k not in seen:
                    seen.add(k)
                    clean.append(k)
            clean_sel[cat] = clean
    note = (raw.get("note") or "").strip()[:400] if isinstance(raw.get("note"), str) else ""
    return {"context_key": ctx or None, "selection": clean_sel, "note": note}


# --------------------------- public (participant) ---------------------------


@bp_agile_scrum_events.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **get_content_for_participant(locale)})


@bp_agile_scrum_events.get("/g/<slug>/state")
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
                AgileTrainingScrumEventsAnswer.query
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
        "exercise_key": sess.exercise_key if sess else "scrum_events",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "content": get_content_for_locale(locale),
        "answer": answer_payload,
    })


@bp_agile_scrum_events.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет выбор участника.

    body:
      {
        "participant_token": "...",
        "selection": {stage: {category: [card_keys]}},
        "errors_seen": ["no_team_on_planning", ...],
        "custom": { "context_key": "...", "selection": {...}, "note": "..." }
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
    errors_seen = _sanitize_errors(body.get("errors_seen"))
    custom = _sanitize_custom(body.get("custom"))

    a = (
        AgileTrainingScrumEventsAnswer.query
        .filter_by(participant_id=p.id)
        .first()
    )
    if not a:
        a = AgileTrainingScrumEventsAnswer(
            group_id=g.id,
            participant_id=p.id,
            data_json="{}",
        )
        db.session.add(a)

    payload = {
        "selection": clean_selection,
        "evaluation": evaluation,
        "errors_seen": errors_seen,
        "custom": custom,
    }
    a.data_json = json.dumps(payload, ensure_ascii=False)
    a.score = int(evaluation["total_score"])
    a.max_score = int(evaluation["total_max"])
    a.health_pct = int(evaluation["health_pct"])

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
        "custom": custom,
    })


# ---- Группа: агрегированные результаты для «сравнения на финале» ----


def _aggregate_group(group_id: int, locale: str) -> Dict:
    """Считает: сколько людей ответили, средний health_pct,
    и для каждого этапа/категории — топ карточек (частоты)."""
    rows = AgileTrainingScrumEventsAnswer.query.filter_by(group_id=group_id).all()
    participants = len(rows)
    if not participants:
        return {
            "participants_count": 0,
            "avg_health_pct": 0,
            "stages": [],
            "errors_seen": [],
        }

    # Частоты: stage -> category -> card_key -> count
    counts: Dict[str, Dict[str, Dict[str, int]]] = {
        s: {c: defaultdict(int) for c in CATEGORIES} for s in STAGE_KEYS
    }
    color_counts: Dict[str, Dict[str, int]] = {
        s: defaultdict(int) for s in STAGE_KEYS
    }
    errors_counter: Dict[str, int] = defaultdict(int)
    total_health = 0

    for r in rows:
        total_health += int(r.health_pct or 0)
        data = _safe_json_load(r.data_json)
        selection = data.get("selection") or {}
        evaluation = (data.get("evaluation") or {}).get("stages") or {}
        for s_key in STAGE_KEYS:
            stage_sel = selection.get(s_key) or {}
            for cat in CATEGORIES:
                for k in (stage_sel.get(cat) or []):
                    counts[s_key][cat][k] += 1
            ev = evaluation.get(s_key) or {}
            col = ev.get("color")
            if col:
                color_counts[s_key][col] += 1
        for err in (data.get("errors_seen") or []):
            errors_counter[err] += 1

    stages_view = []
    for s_key in STAGE_KEYS:
        cat_view = {}
        for cat in CATEGORIES:
            items = counts[s_key][cat]
            top = sorted(items.items(), key=lambda x: -x[1])
            cat_view[cat] = [
                {
                    "key": k,
                    "title": card_title(cat, k, locale),
                    "count": v,
                    "pct": round(v / participants * 100),
                }
                for k, v in top
            ]
        stages_view.append({
            "key": s_key,
            "title": stage_title(s_key, locale),
            "categories": cat_view,
            "colors": dict(color_counts[s_key]),
        })

    errors_view = [
        {"key": k, "count": v, "pct": round(v / participants * 100)}
        for k, v in sorted(errors_counter.items(), key=lambda x: -x[1])
    ]

    return {
        "participants_count": participants,
        "avg_health_pct": round(total_health / participants),
        "stages": stages_view,
        "errors_seen": errors_view,
    }


@bp_agile_scrum_events.get("/g/<slug>/results")
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


@bp_agile_scrum_events.get("/sessions/<int:session_id>/results")
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

    # Лидерборд по health_pct
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


@bp_agile_scrum_events.get("/groups/<int:group_id>/results")
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
        "facilitator_content": get_facilitator_reference_view(locale),
        **_aggregate_group(g.id, locale),
    })


@bp_agile_scrum_events.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Drill-down: per-participant answers для фасилитатора."""
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
            AgileTrainingScrumEventsAnswer.query
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
        evaluation = (data.get("evaluation") or {}).get("stages") or {}
        stages_view = []
        for s_key in STAGE_KEYS:
            stage_sel = selection.get(s_key) or {}
            stage_ev = evaluation.get(s_key) or {}
            cats: Dict[str, Dict] = {}
            for cat in CATEGORIES:
                cat_eval = (stage_ev.get("categories") or {}).get(cat) or {}
                picks = stage_sel.get(cat) or []
                cats[cat] = {
                    "picks": [
                        {"key": k, "title": card_title(cat, k, locale)}
                        for k in picks
                    ],
                    "green": cat_eval.get("green") or [],
                    "yellow": cat_eval.get("yellow") or [],
                    "red": cat_eval.get("red") or [],
                    "missing": cat_eval.get("missing") or [],
                }
            stages_view.append({
                "key": s_key,
                "title": stage_title(s_key, locale),
                "color": stage_ev.get("color"),
                "score": stage_ev.get("score"),
                "max_score": stage_ev.get("max_score"),
                "categories": cats,
            })
        custom = data.get("custom") or None
        errors_seen = data.get("errors_seen") or []
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "has_answer": True,
            "score": a.score,
            "max_score": a.max_score,
            "health_pct": a.health_pct,
            "stages": stages_view,
            "errors_seen": errors_seen,
            "custom": custom,
        })
    return jsonify({"participants": out})


@bp_agile_scrum_events.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    """Удаляет все ответы группы (оставляя самих участников).

    Нужно, чтобы фасилитатор мог пере-запустить упражнение на той же
    группе без пересоздания ссылок."""
    uid = _uid()
    g = AgileTrainingGroup.query.get(group_id)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = _session_for_owner(g.session_id, uid)
    if not sess:
        return jsonify({"error": "Forbidden"}), 403

    (
        AgileTrainingScrumEventsAnswer.query
        .filter_by(group_id=group_id)
        .delete()
    )
    db.session.commit()
    return jsonify({"ok": True})

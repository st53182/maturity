"""Backend тренажёра «Кто отвечает?» (упрощённая версия — без автопроверки).

API под префиксом `/api/agile-training/role-quiz`.

Одна запись на участника (`AgileTrainingRoleQuizAnswer`). В `data_json` лежит:
  - selection[situation_key][role_key] = 'responsible' | 'participates' |
                                          'informed' | 'not_involved' | null
  - submitted: bool — пользователь финализировал ответ для обсуждения
  - submitted_at: ISO timestamp последней отправки

Здесь нет оценок (`score`, `health_pct`): упражнение разбирается вместе с
фасилитатором. Поля БД оставляем как есть для совместимости со схемой —
просто пишем туда `null` или количество отвеченных ситуаций.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

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
    LEVELS,
    ROLE_KEYS,
    SITUATIONS,
    get_content_for_locale,
    level_title,
    role_title,
    sanitize_selection,
    situation_title,
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


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _count_answered(selection: Dict[str, Dict[str, Optional[str]]]) -> int:
    n = 0
    for sit in SITUATIONS:
        row = selection.get(sit["key"]) or {}
        if any(v for v in row.values()):
            n += 1
    return n


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
                    "data": _safe_json_load(a.data_json),
                    "answered": int(a.score or 0),
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
    """Сохраняет/перезаписывает выбор участника.

    body:
      {
        "participant_token": "...",
        "selection": { situation_key: { role_key: level|null } },
        "submitted": bool   # true = «отдал на обсуждение»
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
    submitted = bool(body.get("submitted"))

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
        "submitted": submitted,
        "submitted_at": _now_iso() if submitted else (
            _safe_json_load(a.data_json).get("submitted_at")
        ),
    }
    a.data_json = json.dumps(payload, ensure_ascii=False)
    answered = _count_answered(clean_selection)
    a.score = answered
    a.max_score = len(SITUATIONS)
    a.health_pct = round((answered / len(SITUATIONS)) * 100) if SITUATIONS else 0

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "saved": True,
        "answered": answered,
        "max_situations": len(SITUATIONS),
        "submitted": submitted,
        "submitted_at": payload["submitted_at"],
    })


# --------------------------- aggregation ---------------------------


def _aggregate_group(group_id: int, locale: str) -> Dict:
    """Сводная картина по группе для фасилитатора.

    Не оценивает «правильно/неправильно». Считает, как распределились
    ответы по каждой ячейке (ситуация × роль), и подсвечивает «горячие
    точки» — где у команды нет согласия.
    """
    rows = AgileTrainingRoleQuizAnswer.query.filter_by(group_id=group_id).all()
    submitted_rows: List[AgileTrainingRoleQuizAnswer] = []
    in_progress = 0
    for r in rows:
        data = _safe_json_load(r.data_json)
        if data.get("submitted"):
            submitted_rows.append(r)
        elif data.get("selection"):
            in_progress += 1

    submitted_count = len(submitted_rows)
    if submitted_count == 0:
        return {
            "participants_count": len(rows),
            "submitted_count": 0,
            "in_progress_count": in_progress,
            "situations": [],
            "disagreements": [],
        }

    counts: Dict[str, Dict[str, Dict[str, int]]] = {
        s["key"]: {rk: defaultdict(int) for rk in ROLE_KEYS} for s in SITUATIONS
    }

    for r in submitted_rows:
        data = _safe_json_load(r.data_json)
        selection = data.get("selection") or {}
        for sk in counts.keys():
            for rk in ROLE_KEYS:
                picked = (selection.get(sk) or {}).get(rk)
                counts[sk][rk][picked or "none"] += 1

    situations_view: List[Dict[str, Any]] = []
    disagreement_index: List[Dict[str, Any]] = []

    for s in SITUATIONS:
        sk = s["key"]
        role_view: Dict[str, Dict] = {}
        situation_disagreement = 0
        for rk in ROLE_KEYS:
            level_map = counts[sk][rk]
            items: List[Dict[str, Any]] = []
            non_none_total = 0
            for lk in [*LEVEL_KEYS, "none"]:
                cnt = int(level_map.get(lk, 0) or 0)
                if cnt == 0:
                    continue
                items.append({
                    "level": lk if lk != "none" else None,
                    "level_title": level_title(lk, locale) if lk != "none" else "",
                    "count": cnt,
                    "pct": round(cnt / submitted_count * 100),
                })
                if lk != "none":
                    non_none_total += cnt
            # «Спор»: сколько разных ненулевых вариантов выставили на эту ячейку.
            distinct_levels_picked = sum(
                1 for lk in LEVEL_KEYS if int(level_map.get(lk, 0) or 0) > 0
            )
            role_view[rk] = {
                "levels": items,
                "distinct_picks": distinct_levels_picked,
            }
            if distinct_levels_picked >= 2:
                situation_disagreement += distinct_levels_picked
        situations_view.append({
            "key": sk,
            "title": situation_title(sk, locale),
            "subtitle": (s.get("subtitle") or {}).get(locale)
                or (s.get("subtitle") or {}).get("ru")
                or "",
            "roles": role_view,
            "disagreement_score": situation_disagreement,
        })
        if situation_disagreement > 0:
            disagreement_index.append({
                "key": sk,
                "title": situation_title(sk, locale),
                "score": situation_disagreement,
            })

    disagreement_index.sort(key=lambda x: -x["score"])
    return {
        "participants_count": len(rows),
        "submitted_count": submitted_count,
        "in_progress_count": in_progress,
        "situations": situations_view,
        "disagreements": disagreement_index[:8],
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
    total_submitted = 0
    total_in_progress = 0
    for g in groups:
        agg = _aggregate_group(g.id, locale)
        total_submitted += agg["submitted_count"]
        total_in_progress += agg["in_progress_count"]
        out.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            **agg,
        })

    return jsonify({
        "session": {
            "id": sess.id,
            "title": sess.title,
            "locale": sess.locale,
            "exercise_key": sess.exercise_key,
        },
        "groups": out,
        "totals": {
            "groups_total": len(groups),
            "submitted_total": total_submitted,
            "in_progress_total": total_in_progress,
        },
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
        situations_view = []
        for s in SITUATIONS:
            sk = s["key"]
            sel_roles = selection.get(sk) or {}
            role_view: Dict[str, Dict] = {}
            for rk in ROLE_KEYS:
                picked = sel_roles.get(rk)
                role_view[rk] = {
                    "picked": picked,
                    "picked_title": level_title(picked, locale) if picked else "",
                }
            situations_view.append({
                "key": sk,
                "title": situation_title(sk, locale),
                "roles": role_view,
            })
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "has_answer": True,
            "submitted": bool(data.get("submitted")),
            "submitted_at": data.get("submitted_at"),
            "answered": int(a.score or 0),
            "situations": situations_view,
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

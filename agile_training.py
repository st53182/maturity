"""Backend для раздела Agile Training.

Первое задание — интерактивный тренажёр по 12 принципам Agile
(swipe Tinder-style). Участники проходят без логина по уникальным ссылкам
`/g/<slug>`; фасилитатор (JWT) управляет сессиями/группами и смотрит
агрегацию ответов по группам и сравнение между ними.
"""

from __future__ import annotations

import re
import secrets
from collections import defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingAnswer,
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingRewriteSuggestion,
    AgileTrainingSession,
)
from agile_training_content import AGILE_PRINCIPLES, valid_principle_keys


bp_agile_training = Blueprint(
    "agile_training", __name__, url_prefix="/api/agile-training"
)


ANSWER_VALUES = {"relevant", "outdated"}
ALLOWED_EXERCISE_KEYS = {"agile_principles", "cynefin", "iceberg"}


# --------------------------- helpers ---------------------------


def _uid() -> int:
    return int(get_jwt_identity())


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    """Базовая транслитерация RU → ASCII + очистка до a-z0-9-."""
    if not name:
        return "team"
    s = name.strip().lower()
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
        "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    s = "".join(table.get(ch, ch) for ch in s)
    s = _SLUG_RE.sub("-", s).strip("-")
    s = s[:48] or "team"
    return s


def _make_unique_slug(base: str) -> str:
    """Добавляет короткий случайный суффикс и гарантирует уникальность."""
    for _ in range(8):
        candidate = f"{base}-{secrets.token_hex(3)}"
        if not AgileTrainingGroup.query.filter_by(slug=candidate).first():
            return candidate
    return f"{base}-{secrets.token_hex(6)}"


def _session_for_owner(session_id: int, uid: int) -> Optional[AgileTrainingSession]:
    return AgileTrainingSession.query.filter_by(id=session_id, owner_user_id=uid).first()


def _group_for_owner(group_id: int, uid: int) -> Optional[AgileTrainingGroup]:
    return (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )


ALLOWED_LOCALES = {"ru", "en"}


def _serialize_session(s: AgileTrainingSession, include_groups: bool = False) -> Dict:
    data = {
        "id": s.id,
        "title": s.title or "",
        "exercise_key": s.exercise_key,
        "locale": getattr(s, "locale", None) or "ru",
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "groups_count": s.groups.count(),
    }
    if include_groups:
        data["groups"] = [_serialize_group(g) for g in s.groups.order_by(AgileTrainingGroup.id.asc()).all()]
    return data


def _group_status(participants_count: int, distinct_answer_keys: int, total_principles: int) -> str:
    if participants_count == 0:
        return "not_started"
    if distinct_answer_keys >= total_principles:
        return "completed"
    return "in_progress"


def _serialize_group(g: AgileTrainingGroup) -> Dict:
    participants_count = g.participants.count()
    distinct_keys = (
        db.session.query(AgileTrainingAnswer.principle_key)
        .filter_by(group_id=g.id)
        .distinct()
        .count()
    )
    answers_count = g.answers.count()
    return {
        "id": g.id,
        "session_id": g.session_id,
        "name": g.name,
        "slug": g.slug,
        "participants": participants_count,
        "answers": answers_count,
        "principles_seen": distinct_keys,
        "status": _group_status(participants_count, distinct_keys, len(AGILE_PRINCIPLES)),
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def _principle_by_key(key: str) -> Optional[Dict]:
    for p in AGILE_PRINCIPLES:
        if p["key"] == key:
            return p
    return None


def _aggregate_group_stats(group_id: int) -> Dict[str, Dict]:
    """Для каждого принципа: {relevant, outdated, total, relevant_pct, controversy}."""
    rows = (
        db.session.query(
            AgileTrainingAnswer.principle_key,
            AgileTrainingAnswer.value,
            db.func.count(AgileTrainingAnswer.id),
        )
        .filter_by(group_id=group_id)
        .group_by(AgileTrainingAnswer.principle_key, AgileTrainingAnswer.value)
        .all()
    )
    by_key: Dict[str, Dict[str, int]] = defaultdict(lambda: {"relevant": 0, "outdated": 0})
    for principle_key, value, cnt in rows:
        if value in ANSWER_VALUES:
            by_key[principle_key][value] = int(cnt)

    stats: Dict[str, Dict] = {}
    for p in AGILE_PRINCIPLES:
        r = by_key[p["key"]]["relevant"]
        o = by_key[p["key"]]["outdated"]
        total = r + o
        relevant_pct = round(100 * r / total) if total else 0
        controversy = 100 - abs(relevant_pct - 50) * 2  # 100 = 50/50 split, 0 = всё в одну сторону
        stats[p["key"]] = {
            "relevant": r,
            "outdated": o,
            "total": total,
            "relevant_pct": relevant_pct,
            "outdated_pct": 100 - relevant_pct if total else 0,
            "controversy": controversy if total else 0,
        }
    return stats


def _top_lists(stats: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """Считает топ-3 спорных и очевидных принципов."""
    rows: List[Dict] = []
    for p in AGILE_PRINCIPLES:
        s = stats.get(p["key"], {})
        if not s.get("total"):
            continue
        rows.append({
            "key": p["key"],
            "short": p["short"],
            "relevant_pct": s["relevant_pct"],
            "controversy": s["controversy"],
            "total": s["total"],
        })
    controversial = sorted(rows, key=lambda r: (-r["controversy"], -r["total"]))[:3]
    # «очевидные» = экстремально в одну сторону. Сортируем по |50 - relevant_pct| desc
    obvious = sorted(rows, key=lambda r: (-abs(50 - r["relevant_pct"]), -r["total"]))[:3]
    return {"controversial": controversial, "obvious": obvious}


def _group_compare(session_id: int, focus_group_id: int) -> Dict:
    """Сравнение focus-группы с остальными группами сессии (агрегат по принципам).

    Для каждого принципа считаем relevant% у focus и средний relevant% по остальным.
    Возвращаем топ-3 принципов с наибольшей абсолютной разницей.
    """
    other_group_ids = [
        gid for gid, in db.session.query(AgileTrainingGroup.id)
        .filter(
            AgileTrainingGroup.session_id == session_id,
            AgileTrainingGroup.id != focus_group_id,
        )
        .all()
    ]
    focus_stats = _aggregate_group_stats(focus_group_id)

    others_avg: Dict[str, float] = {}
    others_total_counts: Dict[str, int] = {}
    if other_group_ids:
        for p in AGILE_PRINCIPLES:
            pcts: List[int] = []
            totals = 0
            for gid in other_group_ids:
                st = _aggregate_group_stats(gid).get(p["key"], {})
                if st.get("total"):
                    pcts.append(st["relevant_pct"])
                    totals += st["total"]
            others_avg[p["key"]] = round(sum(pcts) / len(pcts)) if pcts else 0
            others_total_counts[p["key"]] = totals

    diffs: List[Dict] = []
    for p in AGILE_PRINCIPLES:
        f = focus_stats.get(p["key"], {})
        if not f.get("total"):
            continue
        if not other_group_ids or others_total_counts.get(p["key"], 0) == 0:
            continue
        diff = f["relevant_pct"] - others_avg[p["key"]]
        diffs.append({
            "key": p["key"],
            "short": p["short"],
            "this_group_pct": f["relevant_pct"],
            "other_groups_pct": others_avg[p["key"]],
            "diff": diff,
        })
    differences_top = sorted(diffs, key=lambda r: -abs(r["diff"]))[:3]
    return {
        "has_others": bool(other_group_ids),
        "other_groups_count": len(other_group_ids),
        "differences_top": differences_top,
    }


# --------------------------- public content ---------------------------


@bp_agile_training.get("/content/principles")
def content_principles():
    """Возвращает 12 принципов (без связи с группой). Используется хабом/участником."""
    return jsonify({"principles": [dict(p) for p in AGILE_PRINCIPLES]})


# --------------------------- participant endpoints ---------------------------


def _ensure_group_by_slug(slug: str) -> Optional[AgileTrainingGroup]:
    return AgileTrainingGroup.query.filter_by(slug=(slug or "").strip()).first()


@bp_agile_training.get("/g/<slug>")
def group_public(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    session = AgileTrainingSession.query.get(group.session_id)
    return jsonify({
        "group": {
            "id": group.id,
            "name": group.name,
            "slug": group.slug,
        },
        "session": {
            "id": session.id if session else None,
            "title": session.title if session else "",
            "locale": (getattr(session, "locale", None) or "ru") if session else "ru",
            "exercise_key": (getattr(session, "exercise_key", None) or "agile_principles") if session else "agile_principles",
        },
        "principles_total": len(AGILE_PRINCIPLES),
    })


@bp_agile_training.post("/g/<slug>/participant")
def participant_create(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    data = request.get_json(silent=True) or {}
    display_name = (data.get("display_name") or "").strip()[:120] or None

    existing_token = (data.get("participant_token") or "").strip()
    if existing_token:
        p = AgileTrainingParticipant.query.filter_by(
            participant_token=existing_token, group_id=group.id
        ).first()
        if p:
            return jsonify({"participant_token": p.participant_token, "reused": True})

    token = secrets.token_urlsafe(24)
    participant = AgileTrainingParticipant(
        group_id=group.id,
        participant_token=token,
        display_name=display_name,
    )
    db.session.add(participant)
    db.session.commit()
    return jsonify({"participant_token": token, "reused": False})


@bp_agile_training.post("/g/<slug>/answer")
def participant_answer(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    data = request.get_json(silent=True) or {}
    token = (data.get("participant_token") or "").strip()
    principle_key = (data.get("principle_key") or "").strip()
    value = (data.get("value") or "").strip()
    rewrite = (data.get("rewrite") or "").strip()[:2000] or None

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if principle_key not in valid_principle_keys():
        return jsonify({"error": "Unknown principle_key"}), 400
    if value not in ANSWER_VALUES:
        return jsonify({"error": "value must be 'relevant' or 'outdated'"}), 400

    participant = AgileTrainingParticipant.query.filter_by(
        participant_token=token, group_id=group.id
    ).first()
    if not participant:
        return jsonify({"error": "Participant not found in this group"}), 404

    # upsert-логика: один участник — один ответ на принцип
    answer = AgileTrainingAnswer.query.filter_by(
        participant_id=participant.id, principle_key=principle_key
    ).first()
    if answer:
        answer.value = value
        if rewrite is not None:
            answer.rewrite = rewrite
    else:
        answer = AgileTrainingAnswer(
            group_id=group.id,
            participant_id=participant.id,
            principle_key=principle_key,
            value=value,
            rewrite=rewrite,
        )
        db.session.add(answer)
    db.session.commit()

    stats = _aggregate_group_stats(group.id).get(principle_key, {})
    principle = _principle_by_key(principle_key) or {}
    return jsonify({
        "saved": True,
        "stats": stats,
        "provocation": principle.get("provocation", ""),
    })


def _serialize_suggestion(sug: "AgileTrainingRewriteSuggestion", own_token: str = "") -> Dict:
    author = sug.participant
    own = bool(own_token) and author is not None and author.participant_token == own_token
    return {
        "id": sug.id,
        "principle_key": sug.principle_key,
        "text": sug.text,
        "author_name": (author.display_name if author else None),
        "created_at": sug.created_at.isoformat() if sug.created_at else None,
        "own": own,
    }


@bp_agile_training.get("/g/<slug>/rewrite-suggestions")
def rewrite_suggestions_list(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    own_token = (request.args.get("participant_token") or "").strip()

    rows = (
        AgileTrainingRewriteSuggestion.query
        .filter_by(group_id=group.id)
        .order_by(AgileTrainingRewriteSuggestion.created_at.asc())
        .all()
    )
    by_principle: Dict[str, List[Dict]] = defaultdict(list)
    for sug in rows:
        by_principle[sug.principle_key].append(_serialize_suggestion(sug, own_token))
    return jsonify({
        "by_principle": by_principle,
        "total": len(rows),
    })


@bp_agile_training.post("/g/<slug>/rewrite-suggestions")
def rewrite_suggestion_create(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    data = request.get_json(silent=True) or {}
    token = (data.get("participant_token") or "").strip()
    principle_key = (data.get("principle_key") or "").strip()
    text = (data.get("text") or "").strip()

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if principle_key not in valid_principle_keys():
        return jsonify({"error": "Unknown principle_key"}), 400
    if not text:
        return jsonify({"error": "text required"}), 400
    if len(text) > 2000:
        text = text[:2000]

    participant = AgileTrainingParticipant.query.filter_by(
        participant_token=token, group_id=group.id
    ).first()
    if not participant:
        return jsonify({"error": "Participant not found in this group"}), 404

    sug = AgileTrainingRewriteSuggestion(
        group_id=group.id,
        participant_id=participant.id,
        principle_key=principle_key,
        text=text,
    )
    db.session.add(sug)
    db.session.commit()
    return jsonify({"suggestion": _serialize_suggestion(sug, own_token=token)}), 201


@bp_agile_training.delete("/g/<slug>/rewrite-suggestions/<int:sug_id>")
def rewrite_suggestion_delete(slug: str, sug_id: int):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Токен может прийти в body (DELETE с JSON) или в query — принимаем оба варианта.
    token = ""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        token = (data.get("participant_token") or "").strip()
    if not token:
        token = (request.args.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400

    sug = AgileTrainingRewriteSuggestion.query.filter_by(
        id=sug_id, group_id=group.id
    ).first()
    if not sug:
        return jsonify({"error": "Not found"}), 404

    participant = AgileTrainingParticipant.query.filter_by(
        participant_token=token, group_id=group.id
    ).first()
    if not participant or participant.id != sug.participant_id:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(sug)
    db.session.commit()
    return jsonify({"deleted": True})


@bp_agile_training.get("/g/<slug>/results")
def participant_results(slug: str):
    group = _ensure_group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    stats = _aggregate_group_stats(group.id)
    tops = _top_lists(stats)
    compare = _group_compare(group.session_id, group.id)

    per_principle = []
    for p in AGILE_PRINCIPLES:
        s = stats.get(p["key"], {})
        per_principle.append({
            "key": p["key"],
            "short": p["short"],
            "text": p["text"],
            "relevant_pct": s.get("relevant_pct", 0),
            "total": s.get("total", 0),
            "controversy": s.get("controversy", 0),
        })

    return jsonify({
        "group": {"id": group.id, "name": group.name, "slug": group.slug},
        "participants_count": group.participants.count(),
        "per_principle": per_principle,
        "top_controversial": tops["controversial"],
        "top_obvious": tops["obvious"],
        "compare": compare,
    })


# --------------------------- facilitator endpoints ---------------------------


@bp_agile_training.get("/sessions")
@jwt_required()
def sessions_list():
    uid = _uid()
    sessions = (
        AgileTrainingSession.query
        .filter_by(owner_user_id=uid)
        .order_by(AgileTrainingSession.id.desc())
        .all()
    )
    return jsonify({"sessions": [_serialize_session(s) for s in sessions]})


@bp_agile_training.post("/sessions")
@jwt_required()
def sessions_create():
    uid = _uid()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()[:255] or "Agile training"
    locale = (data.get("locale") or "ru").strip().lower()
    if locale not in ALLOWED_LOCALES:
        locale = "ru"
    exercise_key = (data.get("exercise_key") or "agile_principles").strip().lower()
    if exercise_key not in ALLOWED_EXERCISE_KEYS:
        exercise_key = "agile_principles"
    s = AgileTrainingSession(
        owner_user_id=uid,
        title=title,
        exercise_key=exercise_key,
        locale=locale,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(_serialize_session(s, include_groups=True)), 201


@bp_agile_training.get("/sessions/<int:session_id>")
@jwt_required()
def sessions_get(session_id: int):
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_serialize_session(s, include_groups=True))


@bp_agile_training.delete("/sessions/<int:session_id>")
@jwt_required()
def sessions_delete(session_id: int):
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"deleted": True})


@bp_agile_training.post("/sessions/<int:session_id>/groups")
@jwt_required()
def groups_create(session_id: int):
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()[:120] or f"Team {s.groups.count() + 1}"
    slug = _make_unique_slug(_slugify(name))
    g = AgileTrainingGroup(session_id=s.id, name=name, slug=slug)
    db.session.add(g)
    db.session.commit()
    return jsonify(_serialize_group(g)), 201


@bp_agile_training.delete("/groups/<int:group_id>")
@jwt_required()
def groups_delete(group_id: int):
    uid = _uid()
    g = _group_for_owner(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(g)
    db.session.commit()
    return jsonify({"deleted": True})


@bp_agile_training.post("/groups/<int:group_id>/reset")
@jwt_required()
def groups_reset(group_id: int):
    uid = _uid()
    g = _group_for_owner(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404
    AgileTrainingAnswer.query.filter_by(group_id=g.id).delete()
    AgileTrainingParticipant.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})


@bp_agile_training.get("/groups/<int:group_id>/participants")
@jwt_required()
def groups_participants(group_id: int):
    """Детальные ответы каждого участника группы — для фасилитатора,
    чтобы он мог посмотреть, что именно выбрал каждый человек."""
    uid = _uid()
    g = _group_for_owner(group_id, uid)
    if not g:
        return jsonify({"error": "Not found"}), 404

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    principles_index = {p["key"]: p for p in AGILE_PRINCIPLES}
    rows = []
    for idx, p in enumerate(participants, start=1):
        answers = (
            AgileTrainingAnswer.query
            .filter_by(participant_id=p.id)
            .order_by(AgileTrainingAnswer.id.asc())
            .all()
        )
        per_principle = []
        rel = 0
        out = 0
        for a in answers:
            meta = principles_index.get(a.principle_key) or {}
            per_principle.append({
                "principle_key": a.principle_key,
                "short": meta.get("short", a.principle_key),
                "text": meta.get("text", ""),
                "value": a.value,
                "rewrite": a.rewrite,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
            if a.value == "relevant":
                rel += 1
            elif a.value == "outdated":
                out += 1
        suggestions = (
            AgileTrainingRewriteSuggestion.query
            .filter_by(participant_id=p.id)
            .order_by(AgileTrainingRewriteSuggestion.id.asc())
            .all()
        )
        suggestions_out = [
            {
                "id": s.id,
                "principle_key": s.principle_key,
                "short": (principles_index.get(s.principle_key) or {}).get("short", s.principle_key),
                "text": s.text,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suggestions
        ]
        rows.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "answers_total": len(answers),
            "relevant_count": rel,
            "outdated_count": out,
            "answers": per_principle,
            "suggestions": suggestions_out,
        })
    return jsonify({
        "group": _serialize_group(g),
        "participants": rows,
    })


@bp_agile_training.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404

    groups = s.groups.order_by(AgileTrainingGroup.id.asc()).all()
    results = []
    per_group_stats: Dict[int, Dict[str, Dict]] = {}
    for g in groups:
        stats = _aggregate_group_stats(g.id)
        per_group_stats[g.id] = stats
        tops = _top_lists(stats)
        compare = _group_compare(s.id, g.id)
        per_principle = []
        for p in AGILE_PRINCIPLES:
            st = stats.get(p["key"], {})
            per_principle.append({
                "key": p["key"],
                "short": p["short"],
                "relevant_pct": st.get("relevant_pct", 0),
                "total": st.get("total", 0),
                "controversy": st.get("controversy", 0),
            })
        results.append({
            "group": _serialize_group(g),
            "per_principle": per_principle,
            "top_controversial": tops["controversial"],
            "top_obvious": tops["obvious"],
            "compare": compare,
        })

    # общий агрегат по всей сессии
    all_rows = (
        db.session.query(
            AgileTrainingAnswer.principle_key,
            AgileTrainingAnswer.value,
            db.func.count(AgileTrainingAnswer.id),
        )
        .join(AgileTrainingGroup, AgileTrainingGroup.id == AgileTrainingAnswer.group_id)
        .filter(AgileTrainingGroup.session_id == s.id)
        .group_by(AgileTrainingAnswer.principle_key, AgileTrainingAnswer.value)
        .all()
    )
    overall_map: Dict[str, Dict[str, int]] = defaultdict(lambda: {"relevant": 0, "outdated": 0})
    for pk, val, cnt in all_rows:
        if val in ANSWER_VALUES:
            overall_map[pk][val] = int(cnt)
    overall = []
    for p in AGILE_PRINCIPLES:
        r = overall_map[p["key"]]["relevant"]
        o = overall_map[p["key"]]["outdated"]
        total = r + o
        rel_pct = round(100 * r / total) if total else 0
        overall.append({
            "key": p["key"],
            "short": p["short"],
            "relevant_pct": rel_pct,
            "total": total,
        })

    # Сравнение между группами: для каждого принципа — % «Актуально» в каждой группе,
    # разброс (max - min), среднее. Сортируем по разбросу, чтобы увидеть,
    # по каким пунктам команды сильно разошлись.
    cross_group: List[Dict] = []
    for p in AGILE_PRINCIPLES:
        by_group: List[Dict] = []
        pcts: List[int] = []
        total_answers = 0
        for g in groups:
            st = per_group_stats.get(g.id, {}).get(p["key"], {}) or {}
            tot = int(st.get("total", 0) or 0)
            if tot == 0:
                by_group.append({
                    "group_id": g.id,
                    "group_name": g.name,
                    "relevant_pct": None,
                    "total": 0,
                })
                continue
            by_group.append({
                "group_id": g.id,
                "group_name": g.name,
                "relevant_pct": int(st.get("relevant_pct", 0) or 0),
                "total": tot,
            })
            pcts.append(int(st.get("relevant_pct", 0) or 0))
            total_answers += tot
        if pcts:
            spread = max(pcts) - min(pcts)
            avg_pct = round(sum(pcts) / len(pcts))
        else:
            spread = 0
            avg_pct = 0
        principle = _principle_by_key(p["key"]) or {}
        cross_group.append({
            "key": p["key"],
            "short": p["short"],
            "text": principle.get("text", ""),
            "by_group": by_group,
            "spread": spread,
            "avg_relevant_pct": avg_pct,
            "total": total_answers,
            "groups_answered": len(pcts),
        })

    most_split = sorted(
        [r for r in cross_group if r["groups_answered"] >= 2],
        key=lambda r: (-r["spread"], -r["total"]),
    )[:5]
    most_aligned = sorted(
        [r for r in cross_group if r["groups_answered"] >= 2],
        key=lambda r: (r["spread"], -r["total"]),
    )[:5]

    participants_total = sum(g.participants.count() for g in groups)
    answers_total = sum(g.answers.count() for g in groups)

    return jsonify({
        "session": _serialize_session(s),
        "results": results,
        "overall": overall,
        "cross_group": cross_group,
        "most_split": most_split,
        "most_aligned": most_aligned,
        "totals": {
            "groups": len(groups),
            "participants": participants_total,
            "answers": answers_total,
        },
    })

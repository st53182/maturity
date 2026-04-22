"""Backend для упражнения «Айсберг» (системное мышление).

Переиспользует существующие сущности `AgileTrainingSession`,
`AgileTrainingGroup`, `AgileTrainingParticipant` с
`exercise_key = "iceberg"`. Ответы участника по одному кейсу
хранятся одной строкой `AgileTrainingIcebergAnswer` с JSON-полем.

Модель скора «глубина мышления» описана в `iceberg_content.compute_depth_score`.
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
    AgileTrainingIcebergAnswer,
    AgileTrainingParticipant,
    AgileTrainingSession,
)
from iceberg_content import (
    CASES,
    HORIZON_LABELS,
    LEVEL_KEYS,
    LEVEL_WEIGHTS,
    compute_depth_score,
    get_case_debrief,
    get_cases_for_locale,
    get_level_meta,
    level_weight,
    valid_case_keys,
    valid_level_keys,
)


bp_agile_iceberg = Blueprint(
    "agile_iceberg", __name__, url_prefix="/api/agile-training/iceberg"
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


def _sanitize_payload(data: Dict, case_key: str) -> Dict:
    """Приводит вход к стандартной форме, вырезая мусорные поля."""
    expert_items = {it["key"]: it["level"] for c in CASES if c["key"] == case_key for it in c["items"]}
    expert_superficial_keys = {
        s["key"] for c in CASES if c["key"] == case_key for s in c["superficial_explanations"]
    }
    placements = {}
    for k, lv in (data.get("placements") or {}).items():
        if k in expert_items and lv in valid_level_keys():
            placements[k] = lv
    # Дополнительные (свои) карточки: key, text, level — сохраняем текст,
    # но без «правильного уровня» — просто как пользовательские добавки.
    custom_items = []
    for row in (data.get("custom_items") or []):
        text = (row.get("text") or "").strip()[:200]
        lv = row.get("level")
        if not text:
            continue
        if lv not in valid_level_keys():
            lv = None
        custom_items.append({"text": text, "level": lv})
    # Причинная цепочка событие→паттерн→структура→ментальная модель:
    # храним 4 ключа элементов (по одному на уровень), может быть None.
    chain_raw = data.get("chain") or {}
    chain = {}
    for lk in LEVEL_KEYS:
        val = chain_raw.get(lk)
        if isinstance(val, str) and val.strip():
            chain[lk] = val.strip()
    # Классификация поверхностных объяснений: { key: True/False (True = симптом) }
    superficial = {}
    for k, v in (data.get("superficial") or {}).items():
        if k in expert_superficial_keys:
            superficial[k] = bool(v)
    # Интервенции: { level_key: text }
    interventions = {}
    for lk in LEVEL_KEYS:
        raw = (data.get("interventions") or {}).get(lk)
        if isinstance(raw, str):
            interventions[lk] = raw.strip()[:1000]
    return {
        "placements": placements,
        "custom_items": custom_items,
        "chain": chain,
        "superficial": superficial,
        "interventions": interventions,
    }


def _primary_level(interventions: Dict[str, str]) -> Optional[str]:
    """Самый «глубокий» уровень, на котором участник предложил интервенцию."""
    best: Optional[str] = None
    best_weight = -1
    for lk in LEVEL_KEYS:
        txt = (interventions or {}).get(lk)
        if isinstance(txt, str) and txt.strip():
            w = LEVEL_WEIGHTS.get(lk, 0)
            if w > best_weight:
                best = lk
                best_weight = w
    return best


def _aggregate_case_stats(group_id: int, case_key: str) -> Dict:
    """Группирует ответы по case_key и считает агрегаты.

    Возвращает:
      total                  — количество ответов
      placements_by_item     — { item_key: { level: pct, ... } }
      superficial_correct_pct — { sup_key: pct правильных классификаций }
      intervention_levels    — { level: pct участников, кто предложил интервенцию }
      primary_level_counts   — { level: count } — главный уровень мышления
      avg_score              — средний depth_score
    """
    rows = AgileTrainingIcebergAnswer.query.filter_by(
        group_id=group_id, case_key=case_key
    ).all()
    total = len(rows)
    placements_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    superficial_counts: Dict[str, int] = defaultdict(int)
    superficial_totals: Dict[str, int] = defaultdict(int)
    intervention_counts: Dict[str, int] = defaultdict(int)
    primary_level_counts: Dict[str, int] = defaultdict(int)
    score_sum = 0
    expert_items_map = {it["key"]: it["level"] for c in CASES if c["key"] == case_key for it in c["items"]}
    expert_sup_map = {
        s["key"]: s["is_symptom"]
        for c in CASES if c["key"] == case_key for s in c["superficial_explanations"]
    }
    for r in rows:
        data = _safe_json_load(r.data_json)
        for ik, lv in (data.get("placements") or {}).items():
            if lv in LEVEL_KEYS:
                placements_counts[ik][lv] += 1
        for sk, val in (data.get("superficial") or {}).items():
            if sk in expert_sup_map:
                superficial_totals[sk] += 1
                if bool(val) == bool(expert_sup_map[sk]):
                    superficial_counts[sk] += 1
        for lk in LEVEL_KEYS:
            txt = (data.get("interventions") or {}).get(lk)
            if isinstance(txt, str) and txt.strip():
                intervention_counts[lk] += 1
        if r.primary_level in LEVEL_KEYS:
            primary_level_counts[r.primary_level] += 1
        score_sum += int(r.depth_score or 0)

    placements_by_item: Dict[str, Dict[str, int]] = {}
    for ik, by_level in placements_counts.items():
        sub_total = sum(by_level.values())
        placements_by_item[ik] = {
            lk: (round(100 * by_level.get(lk, 0) / sub_total) if sub_total else 0)
            for lk in LEVEL_KEYS
        }
        placements_by_item[ik]["expert"] = expert_items_map.get(ik)

    superficial_correct_pct = {
        sk: (round(100 * superficial_counts[sk] / superficial_totals[sk])
             if superficial_totals[sk] else 0)
        for sk in expert_sup_map
    }
    intervention_pct = {
        lk: (round(100 * intervention_counts[lk] / total) if total else 0)
        for lk in LEVEL_KEYS
    }
    primary_pct = {
        lk: (round(100 * primary_level_counts.get(lk, 0) / total) if total else 0)
        for lk in LEVEL_KEYS
    }
    avg_score = round(score_sum / total, 1) if total else 0.0

    return {
        "total": total,
        "placements_by_item": placements_by_item,
        "superficial_correct_pct": superficial_correct_pct,
        "intervention_pct": intervention_pct,
        "primary_level_counts": dict(primary_level_counts),
        "primary_level_pct": primary_pct,
        "avg_score": avg_score,
    }


def _aggregate_group_totals(group_id: int) -> Dict:
    rows = AgileTrainingIcebergAnswer.query.filter_by(group_id=group_id).all()
    total = len(rows)
    primary_counts: Dict[str, int] = defaultdict(int)
    score_sum = 0
    for r in rows:
        if r.primary_level in LEVEL_KEYS:
            primary_counts[r.primary_level] += 1
        score_sum += int(r.depth_score or 0)
    primary_pct = {
        lk: (round(100 * primary_counts.get(lk, 0) / total) if total else 0)
        for lk in LEVEL_KEYS
    }
    avg_score = round(score_sum / total, 1) if total else 0.0
    return {
        "answers": total,
        "primary_level_pct": primary_pct,
        "primary_level_counts": dict(primary_counts),
        "avg_score": avg_score,
    }


def _participant_answers_map(participant_id: int) -> Dict[str, Dict]:
    rows = AgileTrainingIcebergAnswer.query.filter_by(
        participant_id=participant_id
    ).all()
    out: Dict[str, Dict] = {}
    for r in rows:
        data = _safe_json_load(r.data_json)
        out[r.case_key] = {
            "data": data,
            "depth_score": int(r.depth_score or 0),
            "primary_level": r.primary_level,
        }
    return out


# --------------------------- public content ---------------------------


@bp_agile_iceberg.get("/content")
def content_public():
    """Список кейсов с карточками + описание уровней айсберга."""
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({
        "locale": locale,
        "levels": get_level_meta(locale),
        "horizons": {k: HORIZON_LABELS[k][("en" if locale == "en" else "ru")] for k in HORIZON_LABELS},
        "cases": get_cases_for_locale(locale),
    })


@bp_agile_iceberg.get("/cases/<case_key>/debrief")
def case_debrief(case_key: str):
    locale = _resolve_locale(request.args.get("locale"), None)
    debrief = get_case_debrief(case_key, locale)
    if not debrief:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(debrief)


# --------------------------- participant ---------------------------


@bp_agile_iceberg.get("/g/<slug>/state")
def participant_state(slug: str):
    group = _group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    token = (request.args.get("participant_token") or "").strip()
    answered: Dict[str, Dict] = {}
    if token:
        participant = AgileTrainingParticipant.query.filter_by(
            participant_token=token, group_id=group.id
        ).first()
        if participant:
            answered = _participant_answers_map(participant.id)
    return jsonify({"answered": answered, "total": len(CASES)})


@bp_agile_iceberg.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет (upsert) полный разбор одного кейса.

    Body:
      participant_token: str
      case_key:          str
      placements:        { item_key: level_key }  — как участник разложил карточки
      custom_items:      [ { text, level } ]       — свои добавленные карточки (опционально)
      chain:             { level_key: item_key }   — причинная цепочка (event->pattern->…)
      superficial:       { sup_key: bool }         — True = «это симптом/поверхностное»
      interventions:     { level_key: text }       — решения на каждом уровне
      locale:            'ru'|'en'                 — для языка дебрифа

    Возвращает дебриф и агрегированную статистику группы по этому кейсу.
    """
    group = _group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    data = request.get_json(silent=True) or {}
    token = (data.get("participant_token") or "").strip()
    case_key = (data.get("case_key") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if case_key not in valid_case_keys():
        return jsonify({"error": "Unknown case_key"}), 400

    participant = AgileTrainingParticipant.query.filter_by(
        participant_token=token, group_id=group.id
    ).first()
    if not participant:
        return jsonify({"error": "Participant not found in this group"}), 404

    payload = _sanitize_payload(data, case_key)

    debrief = get_case_debrief(case_key, _resolve_locale(data.get("locale"),
                                                        AgileTrainingSession.query.get(group.session_id)))
    score_parts = compute_depth_score(
        placements=payload["placements"],
        expert_items=debrief["items_expert"],
        superficial_answers=payload["superficial"],
        superficial_expert=debrief["superficial_expert"],
        interventions=payload["interventions"],
    )
    total_score = int(score_parts["total"])
    primary = _primary_level(payload["interventions"])

    row = AgileTrainingIcebergAnswer.query.filter_by(
        participant_id=participant.id, case_key=case_key
    ).first()
    if row:
        row.data_json = json.dumps(payload, ensure_ascii=False)
        row.depth_score = total_score
        row.primary_level = primary
    else:
        row = AgileTrainingIcebergAnswer(
            group_id=group.id,
            participant_id=participant.id,
            case_key=case_key,
            data_json=json.dumps(payload, ensure_ascii=False),
            depth_score=total_score,
            primary_level=primary,
        )
        db.session.add(row)
    db.session.commit()

    stats = _aggregate_case_stats(group.id, case_key)

    return jsonify({
        "saved": True,
        "depth_score": total_score,
        "score_parts": score_parts,
        "primary_level": primary,
        "debrief": debrief,
        "stats": stats,
    })


@bp_agile_iceberg.get("/g/<slug>/results")
def participant_results(slug: str):
    group = _group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    session = AgileTrainingSession.query.get(group.session_id)
    locale = _resolve_locale(request.args.get("locale"), session)
    token = (request.args.get("participant_token") or "").strip()

    my_answers: Dict[str, Dict] = {}
    participant_id: Optional[int] = None
    if token:
        participant = AgileTrainingParticipant.query.filter_by(
            participant_token=token, group_id=group.id
        ).first()
        if participant:
            participant_id = participant.id
            my_answers = _participant_answers_map(participant.id)

    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}
    per_case: List[Dict] = []
    my_total = 0
    my_primary_counts: Dict[str, int] = defaultdict(int)
    for c in CASES:
        key = c["key"]
        stats = _aggregate_case_stats(group.id, key)
        my = my_answers.get(key, {})
        if my:
            my_total += int(my.get("depth_score", 0) or 0)
            pl = my.get("primary_level")
            if pl:
                my_primary_counts[pl] += 1
        per_case.append({
            "key": key,
            "order": cases_loc[key]["order"],
            "title": cases_loc[key]["title"],
            "category": cases_loc[key]["category"],
            "scenario": cases_loc[key]["scenario"],
            "stats": stats,
            "my": my,
        })

    group_totals = _aggregate_group_totals(group.id)

    # «глубина мышления» участника = средний скор по сделанным кейсам
    my_count = sum(1 for a in my_answers.values() if a)
    my_avg = round(my_total / my_count, 1) if my_count else 0.0

    return jsonify({
        "group": {"id": group.id, "name": group.name, "slug": group.slug},
        "locale": locale,
        "participants_count": group.participants.count(),
        "per_case": per_case,
        "group_totals": group_totals,
        "my": {
            "answered": my_count,
            "avg_score": my_avg,
            "primary_level_counts": dict(my_primary_counts),
        },
    })


# --------------------------- facilitator ---------------------------


@bp_agile_iceberg.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    """Сводка по всей сессии + сравнение групп (distribution по primary_level)."""
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), s)
    groups = s.groups.order_by(AgileTrainingGroup.id.asc()).all()

    groups_summary: List[Dict] = []
    for g in groups:
        participants_count = g.participants.count()
        ans_rows = AgileTrainingIcebergAnswer.query.filter_by(group_id=g.id).all()
        answers_count = len(ans_rows)
        distinct_cases = len({r.case_key for r in ans_rows})
        if participants_count == 0:
            status = "not_started"
        elif distinct_cases >= len(CASES):
            status = "completed"
        else:
            status = "in_progress"
        totals = _aggregate_group_totals(g.id)
        groups_summary.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants": participants_count,
            "answers": answers_count,
            "cases_seen": distinct_cases,
            "status": status,
            "avg_score": totals["avg_score"],
            "primary_level_pct": totals["primary_level_pct"],
        })

    # «самые системные» / «самые поверхностные» кейсы по среднему depth_score
    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}
    per_case_stats = []
    for c in CASES:
        key = c["key"]
        per_group = []
        scores = []
        for g in groups:
            st = _aggregate_case_stats(g.id, key)
            per_group.append({
                "group_id": g.id,
                "group_name": g.name,
                "total": st["total"],
                "avg_score": st["avg_score"],
                "primary_level_pct": st["primary_level_pct"],
            })
            if st["total"]:
                scores.append(st["avg_score"])
        spread = (max(scores) - min(scores)) if len(scores) >= 2 else 0
        per_case_stats.append({
            "key": key,
            "title": cases_loc[key]["title"],
            "category": cases_loc[key]["category"],
            "by_group": per_group,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "spread": round(spread, 1),
            "groups_answered": len(scores),
        })

    most_split = sorted(
        [r for r in per_case_stats if r["groups_answered"] >= 2],
        key=lambda r: (-r["spread"], -r["avg_score"])
    )[:5]

    totals = {
        "groups": len(groups),
        "participants": sum(gs["participants"] for gs in groups_summary),
        "answers": sum(gs["answers"] for gs in groups_summary),
    }

    return jsonify({
        "session": {
            "id": s.id,
            "title": s.title,
            "locale": s.locale,
            "exercise_key": s.exercise_key,
        },
        "groups": groups_summary,
        "per_case": per_case_stats,
        "most_split": most_split,
        "totals": totals,
    })


@bp_agile_iceberg.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results_facilitator(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404
    locale = _resolve_locale(request.args.get("locale"),
                             AgileTrainingSession.query.get(g.session_id))
    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}
    per_case: List[Dict] = []
    for c in CASES:
        key = c["key"]
        stats = _aggregate_case_stats(g.id, key)
        debrief = get_case_debrief(key, locale) or {}
        per_case.append({
            "key": key,
            "title": cases_loc[key]["title"],
            "category": cases_loc[key]["category"],
            "scenario": cases_loc[key]["scenario"],
            "stats": stats,
            "summary": debrief.get("summary", ""),
            "interventions_expert": debrief.get("interventions_expert", {}),
        })
    totals = _aggregate_group_totals(g.id)
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "group_totals": totals,
        "per_case": per_case,
    })


@bp_agile_iceberg.post("/groups/<int:group_id>/reset")
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
    AgileTrainingIcebergAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})

"""Backend для тренажёра «MVP → MMP → MLP» (продуктовое мышление).

Переиспользует сущности `AgileTrainingSession` / `AgileTrainingGroup` /
`AgileTrainingParticipant` (exercise_key = "mvp") и собственную таблицу
ответов `AgileTrainingMvpAnswer` — одна запись на (participant, case).

Логика «проверки гипотезы / MMP / MLP» полностью лежит в `mvp_content`.
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
    AgileTrainingMvpAnswer,
    AgileTrainingParticipant,
    AgileTrainingSession,
)
from mvp_content import (
    CASES,
    STAGE_KEYS,
    STAGE_LIMITS,
    evaluate_iteration,
    get_cases_for_locale,
    total_score,
    valid_case_keys,
)


bp_agile_mvp = Blueprint(
    "agile_mvp", __name__, url_prefix="/api/agile-training/mvp"
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


def _feature_keys(case_key: str) -> set:
    for c in CASES:
        if c["key"] == case_key:
            return {f["key"] for f in c["features"]}
    return set()


def _sanitize_features(case_key: str, features: List[str]) -> List[str]:
    valid = _feature_keys(case_key)
    seen: List[str] = []
    for k in features or []:
        if isinstance(k, str) and k in valid and k not in seen:
            seen.append(k)
    return seen


def _build_stage_view(case_key: str, stage: str, features: List[str]) -> Dict:
    """Собирает результат итерации для UI: статус, реакция (2 локали),
    антипаттерны, подсказки, счётчики. Локализация финальная — на клиенте."""
    features = _sanitize_features(case_key, features)
    res = evaluate_iteration(case_key, stage, features)
    return {
        "stage": stage,
        "selected": features,
        "status": res["status"],
        "counts": res["counts"],
        "limit": res["limit"],
        "antipatterns": res["antipatterns"],
        "hint_keys": res["hint_keys"],
        "reaction_locales": res["reaction_text_locales"],
    }


def _recompute_answer(answer: AgileTrainingMvpAnswer) -> None:
    """Пересчитывает статус каждой итерации и total_score и пишет их в поле."""
    data = _safe_json_load(answer.data_json)
    case_key = answer.case_key

    stages_out: Dict[str, Dict] = {}
    last_filled: Optional[str] = None
    statuses = {"mvp": None, "mmp": None, "mlp": None}

    for stage in STAGE_KEYS:
        st = data.get(stage) or {}
        features = _sanitize_features(case_key, st.get("features") or [])
        if not features:
            # итерация не начата
            stages_out[stage] = {"features": [], "status": None}
            continue
        res = evaluate_iteration(case_key, stage, features)
        stages_out[stage] = {"features": features, "status": res["status"]}
        statuses[stage] = res["status"]
        last_filled = stage

    answer.data_json = json.dumps(stages_out, ensure_ascii=False)
    answer.total_score = total_score(statuses["mvp"], statuses["mmp"], statuses["mlp"])
    answer.final_stage = last_filled


# --------------------------- public ---------------------------


@bp_agile_mvp.get("/content")
def content_public():
    """Публичный контент: кейсы + фичи + лимиты."""
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({
        "locale": locale,
        "stages": STAGE_KEYS,
        "stage_limits": dict(STAGE_LIMITS),
        "cases": get_cases_for_locale(locale),
    })


@bp_agile_mvp.get("/g/<slug>/state")
def participant_state(slug: str):
    """Возвращает текущий прогресс участника по каждому кейсу."""
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404
    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)

    token = (request.args.get("participant_token") or "").strip()
    answers: Dict[str, Dict] = {}
    if token:
        participant = (
            AgileTrainingParticipant.query
            .filter_by(group_id=g.id, participant_token=token)
            .first()
        )
        if participant:
            rows = AgileTrainingMvpAnswer.query.filter_by(
                participant_id=participant.id
            ).all()
            for r in rows:
                answers[r.case_key] = _safe_json_load(r.data_json)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "exercise_key": sess.exercise_key if sess else "mvp",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "cases": get_cases_for_locale(locale),
        "answers": answers,
        "stages": STAGE_KEYS,
        "stage_limits": dict(STAGE_LIMITS),
    })


@bp_agile_mvp.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет выбор участника на одной из итераций и возвращает результат.

    body: {
      participant_token: "...",
      case_key: "taxi",
      stage: "mvp" | "mmp" | "mlp",
      features: ["pickup","price","callcar"]
    }
    """
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    data = request.get_json(silent=True) or {}
    token = (data.get("participant_token") or "").strip()
    case_key = (data.get("case_key") or "").strip()
    stage = (data.get("stage") or "").strip()
    features = data.get("features") or []

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if case_key not in valid_case_keys():
        return jsonify({"error": "unknown case"}), 400
    if stage not in STAGE_KEYS:
        return jsonify({"error": "unknown stage"}), 400

    participant = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id, participant_token=token)
        .first()
    )
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    features = _sanitize_features(case_key, features)[: STAGE_LIMITS[stage]]

    # Валидация: MMP / MLP расширяют предыдущую итерацию, не сужают.
    # Берём существующий ответ, если есть.
    answer = (
        AgileTrainingMvpAnswer.query
        .filter_by(participant_id=participant.id, case_key=case_key)
        .first()
    )
    if answer:
        prev = _safe_json_load(answer.data_json)
    else:
        prev = {}

    if stage == "mmp":
        mvp_prev = _sanitize_features(case_key, (prev.get("mvp") or {}).get("features") or [])
        for k in mvp_prev:
            if k not in features:
                features.append(k)
        features = features[: STAGE_LIMITS["mmp"]]
    elif stage == "mlp":
        mmp_prev = _sanitize_features(case_key, (prev.get("mmp") or {}).get("features") or [])
        for k in mmp_prev:
            if k not in features:
                features.append(k)
        features = features[: STAGE_LIMITS["mlp"]]

    if not answer:
        answer = AgileTrainingMvpAnswer(
            group_id=g.id,
            participant_id=participant.id,
            case_key=case_key,
            data_json=json.dumps({}, ensure_ascii=False),
        )
        db.session.add(answer)

    data_cur = _safe_json_load(answer.data_json)
    data_cur[stage] = {"features": features}
    # Если перезаписали более раннюю стадию (например, MVP поменяли) —
    # делаем старшие стадии «пустыми», чтобы участник их переиграл осознанно.
    if stage == "mvp":
        data_cur["mmp"] = {"features": []}
        data_cur["mlp"] = {"features": []}
    elif stage == "mmp":
        data_cur["mlp"] = {"features": []}
    answer.data_json = json.dumps(data_cur, ensure_ascii=False)

    _recompute_answer(answer)
    db.session.commit()

    return jsonify({
        "saved": True,
        "stage_result": _build_stage_view(case_key, stage, features),
        "data": _safe_json_load(answer.data_json),
        "total_score": answer.total_score,
        "final_stage": answer.final_stage,
    })


@bp_agile_mvp.get("/g/<slug>/results")
def participant_results(slug: str):
    """Агрегированные результаты по группе для экрана команды."""
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)

    cases = get_cases_for_locale(locale)
    rows = AgileTrainingMvpAnswer.query.filter_by(group_id=g.id).all()

    # per-case агрегация выбора фич и статусов
    by_case_feature: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_case_totals: Dict[str, int] = defaultdict(int)
    by_case_status: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    score_sum = 0
    for r in rows:
        payload = _safe_json_load(r.data_json)
        # уникальные выбранные фичи за весь кейс (max стадия)
        all_features: List[str] = []
        for stage in STAGE_KEYS:
            st = payload.get(stage) or {}
            for k in (st.get("features") or []):
                if k not in all_features:
                    all_features.append(k)
            if st.get("status"):
                by_case_status[r.case_key][stage][st["status"]] += 1
        by_case_totals[r.case_key] += 1
        for k in all_features:
            by_case_feature[r.case_key][k] += 1
        score_sum += int(r.total_score or 0)

    per_case = []
    for c in cases:
        total = by_case_totals.get(c["key"], 0)
        # top features для группы
        feature_stats = []
        for f in c["features"]:
            cnt = by_case_feature.get(c["key"], {}).get(f["key"], 0)
            feature_stats.append({
                "key": f["key"],
                "title": f["title"],
                "weight": f["weight"],
                "expected_stage": f["expected_stage"],
                "count": cnt,
                "pct": round(100 * cnt / total) if total else 0,
            })
        stage_status_pct = {}
        for stage in STAGE_KEYS:
            s = by_case_status.get(c["key"], {}).get(stage, {})
            tot = sum(s.values()) or 0
            stage_status_pct[stage] = {
                k: (round(100 * v / tot) if tot else 0) for k, v in s.items()
            }
            stage_status_pct[stage]["total"] = tot
        per_case.append({
            "key": c["key"],
            "title": c["title"],
            "category": c["category"],
            "total_answers": total,
            "features": feature_stats,
            "stage_status_pct": stage_status_pct,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "avg_score": round(score_sum / len(rows), 1) if rows else 0.0,
        "per_case": per_case,
    })


# --------------------------- facilitator ---------------------------


@bp_agile_mvp.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    """Кросс-групповое сравнение: быстрее проверили гипотезу и лучший продукт."""
    uid = _uid()
    sess = _session_for_owner(session_id, uid)
    if not sess:
        return jsonify({"error": "Not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), sess)
    cases = get_cases_for_locale(locale)
    groups = sess.groups.order_by(AgileTrainingGroup.id.asc()).all()

    groups_view = []
    totals = {"groups": 0, "participants": 0, "answers": 0}
    for g in groups:
        rows = AgileTrainingMvpAnswer.query.filter_by(group_id=g.id).all()
        participants = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants
        totals["answers"] += len(rows)

        # статистика статусов по итерациям
        stage_success_pct: Dict[str, float] = {}
        for stage in STAGE_KEYS:
            success = 0
            total = 0
            for r in rows:
                st = (_safe_json_load(r.data_json).get(stage) or {})
                if st.get("status"):
                    total += 1
                    if st["status"] == "success":
                        success += 1
            stage_success_pct[stage] = round(100 * success / total) if total else 0

        avg_score = round(sum((r.total_score or 0) for r in rows) / len(rows), 1) if rows else 0.0
        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants,
            "answers_count": len(rows),
            "avg_score": avg_score,
            "stage_success_pct": stage_success_pct,
        })

    # Лидерборды: быстрее всех проверили гипотезу = максимум MVP success
    fastest = sorted(
        groups_view, key=lambda g: (-g["stage_success_pct"].get("mvp", 0), g["id"])
    )
    best = sorted(
        groups_view, key=lambda g: (-g["avg_score"], g["id"])
    )

    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "cases": cases,
        "totals": totals,
        "groups": groups_view,
        "leaderboard_fastest": fastest,
        "leaderboard_best": best,
    })


@bp_agile_mvp.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    """Детали одной группы для фасилитатора (какие фичи выбирали, распределение статусов)."""
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
    cases = get_cases_for_locale(locale)

    rows = AgileTrainingMvpAnswer.query.filter_by(group_id=g.id).all()
    by_case_feature: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_case_status: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    by_case_total: Dict[str, int] = defaultdict(int)
    for r in rows:
        payload = _safe_json_load(r.data_json)
        by_case_total[r.case_key] += 1
        seen: List[str] = []
        for stage in STAGE_KEYS:
            st = payload.get(stage) or {}
            for k in (st.get("features") or []):
                if k not in seen:
                    seen.append(k)
            if st.get("status"):
                by_case_status[r.case_key][stage][st["status"]] += 1
        for k in seen:
            by_case_feature[r.case_key][k] += 1

    per_case = []
    for c in cases:
        total = by_case_total.get(c["key"], 0)
        feature_stats = []
        for f in c["features"]:
            cnt = by_case_feature.get(c["key"], {}).get(f["key"], 0)
            feature_stats.append({
                "key": f["key"],
                "title": f["title"],
                "weight": f["weight"],
                "expected_stage": f["expected_stage"],
                "count": cnt,
                "pct": round(100 * cnt / total) if total else 0,
            })
        stage_status = {}
        for stage in STAGE_KEYS:
            s = by_case_status.get(c["key"], {}).get(stage, {})
            tot = sum(s.values()) or 0
            stage_status[stage] = {
                "total": tot,
                "success": s.get("success", 0),
                "partial": s.get("partial", 0),
                "fail": s.get("fail", 0),
                "pct": {
                    "success": round(100 * s.get("success", 0) / tot) if tot else 0,
                    "partial": round(100 * s.get("partial", 0) / tot) if tot else 0,
                    "fail": round(100 * s.get("fail", 0) / tot) if tot else 0,
                },
            }
        per_case.append({
            "key": c["key"],
            "title": c["title"],
            "category": c["category"],
            "hypothesis": c["hypothesis"],
            "total_answers": total,
            "features": feature_stats,
            "stage_status": stage_status,
        })

    avg_score = round(sum((r.total_score or 0) for r in rows) / len(rows), 1) if rows else 0.0
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "avg_score": avg_score,
        "per_case": per_case,
    })


@bp_agile_mvp.post("/groups/<int:group_id>/reset")
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
    AgileTrainingMvpAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})


@bp_agile_mvp.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детальные ответы каждого участника: какие фичи выбрали на MVP/MMP/MLP и статусы."""
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
    cases = get_cases_for_locale(locale)
    cases_index = {c["key"]: c for c in cases}

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows_out = []
    for idx, p in enumerate(participants, start=1):
        answers = (
            AgileTrainingMvpAnswer.query
            .filter_by(participant_id=p.id)
            .order_by(AgileTrainingMvpAnswer.id.asc())
            .all()
        )
        per_case = []
        for a in answers:
            payload = _safe_json_load(a.data_json)
            case = cases_index.get(a.case_key) or {}
            fmap = {f["key"]: f for f in (case.get("features") or [])}
            stages_view = {}
            for stage in STAGE_KEYS:
                st = payload.get(stage) or {}
                feats = [
                    {
                        "key": k,
                        "title": (fmap.get(k) or {}).get("title", k),
                        "weight": (fmap.get(k) or {}).get("weight", "optional"),
                        "expected_stage": (fmap.get(k) or {}).get("expected_stage"),
                    }
                    for k in (st.get("features") or [])
                ]
                stages_view[stage] = {
                    "features": feats,
                    "status": st.get("status"),
                }
            per_case.append({
                "case_key": a.case_key,
                "case_title": case.get("title", a.case_key),
                "case_category": case.get("category", ""),
                "total_score": int(a.total_score or 0),
                "final_stage": a.final_stage,
                "stages": stages_view,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            })

        rows_out.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "cases_answered": len(answers),
            "total_score": sum(int(a.total_score or 0) for a in answers),
            "answers": per_case,
        })
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows_out,
    })

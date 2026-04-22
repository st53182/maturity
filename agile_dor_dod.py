"""Backend тренажёра Definition of Ready / Definition of Done.

API под префиксом `/api/agile-training/dor-dod`.

Использует общие сущности обучающего каркаса:
  - AgileTrainingSession (exercise_key = "dor_dod")
  - AgileTrainingGroup
  - AgileTrainingParticipant

Ответы храним одной записью на участника — у нас сценарий без
множества кейсов, зато с двумя итерациями (initial + improved).
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingDorDodAnswer,
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingSession,
)
from dor_dod_content import (
    EFFECTS,
    RULES,
    TEAM_TYPES,
    evaluate_round,
    get_content_for_locale,
    improvement_delta,
    sanitize_round,
    simulate_outcome,
    valid_effect_keys,
    valid_rule_keys,
    valid_team_keys,
)


bp_agile_dor_dod = Blueprint(
    "agile_dor_dod", __name__, url_prefix="/api/agile-training/dor-dod"
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


def _stage_from_round(round_key: str) -> str:
    return "improved" if round_key == "improved" else "initial"


def _apply_round(answer: AgileTrainingDorDodAnswer, round_key: str, payload: Dict) -> Dict:
    """Записывает раунд (initial / improved) в answer.data_json, пересчитывает
    eval и outcome, пишет score / outcome в отдельные поля."""
    data = _safe_json_load(answer.data_json)
    data.setdefault("initial", None)
    data.setdefault("improved", None)
    data.setdefault("eval_initial", None)
    data.setdefault("eval_improved", None)

    clean = sanitize_round(payload)
    evaluation = evaluate_round(answer.team_key, clean)
    outcome = simulate_outcome(answer.team_key, evaluation)

    if round_key == "improved":
        data["improved"] = clean
        data["eval_improved"] = evaluation
        data["sim_improved"] = outcome
        answer.score_improved = float(evaluation.get("score_raw") or 0)
        answer.outcome_improved = outcome.get("outcome")
    else:
        data["initial"] = clean
        data["eval_initial"] = evaluation
        data["sim_initial"] = outcome
        data["improved"] = None
        data["eval_improved"] = None
        data["sim_improved"] = None
        answer.score_initial = float(evaluation.get("score_raw") or 0)
        answer.outcome_initial = outcome.get("outcome")
        answer.score_improved = None
        answer.outcome_improved = None

    answer.data_json = json.dumps(data, ensure_ascii=False)
    return {
        "round": round_key,
        "clean": clean,
        "eval": evaluation,
        "simulation": outcome,
    }


# --------------------------- public (participant) ---------------------------


@bp_agile_dor_dod.get("/content")
def content_public():
    """Публичный контент: команды, карточки, эффекты."""
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **get_content_for_locale(locale)})


@bp_agile_dor_dod.get("/g/<slug>/state")
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
                AgileTrainingDorDodAnswer.query
                .filter_by(participant_id=p.id)
                .first()
            )
            if a:
                answer_payload = {
                    "team_key": a.team_key,
                    "data": _safe_json_load(a.data_json),
                }

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "exercise_key": sess.exercise_key if sess else "dor_dod",
        "session_locale": sess.locale if sess else "ru",
        "effective_locale": locale,
        "content": get_content_for_locale(locale),
        "answer": answer_payload,
    })


@bp_agile_dor_dod.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет раунд участника.

    body:
      {
        "participant_token": "...",
        "team_key": "it" | "marketing" | "ops",
        "round": "initial" | "improved",
        "dor": [...], "dod": [...], "mapping": {rule: [effects]}
      }
    """
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    team_key = (body.get("team_key") or "").strip()
    round_key = _stage_from_round(body.get("round") or "initial")

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if team_key not in valid_team_keys():
        return jsonify({"error": "unknown team_key"}), 400

    p = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id, participant_token=token)
        .first()
    )
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = (
        AgileTrainingDorDodAnswer.query
        .filter_by(participant_id=p.id)
        .first()
    )
    if not a:
        a = AgileTrainingDorDodAnswer(
            group_id=g.id,
            participant_id=p.id,
            team_key=team_key,
            data_json=json.dumps({}, ensure_ascii=False),
        )
        db.session.add(a)
    else:
        # Не позволяем менять тип команды посредине упражнения, кроме
        # случая, когда пришёл round="initial" — тогда разрешаем пересобрать.
        if round_key == "initial":
            a.team_key = team_key
        elif a.team_key != team_key:
            return jsonify({"error": "team_key mismatch for improved round"}), 400

    try:
        result = _apply_round(a, round_key, body)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    db.session.commit()

    data_all = _safe_json_load(a.data_json)
    delta = improvement_delta(
        data_all.get("eval_initial"),
        data_all.get("eval_improved"),
    )

    return jsonify({
        "saved": True,
        "team_key": a.team_key,
        "round": round_key,
        "clean": result["clean"],
        "eval": result["eval"],
        "simulation": result["simulation"],
        "delta": delta,
    })


@bp_agile_dor_dod.get("/g/<slug>/results")
def participant_results(slug: str):
    """Агрегированные результаты группы — для экрана «сравнение» на
    финальной странице участника."""
    g = _group_by_slug(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    sess = AgileTrainingSession.query.get(g.session_id)
    locale = _resolve_locale(request.args.get("locale"), sess)
    content = get_content_for_locale(locale)

    rows = AgileTrainingDorDodAnswer.query.filter_by(group_id=g.id).all()

    per_team: Dict[str, Dict] = defaultdict(lambda: {
        "participants": 0,
        "improved": 0,
        "avg_initial": 0.0,
        "avg_improved": 0.0,
        "dor_counts": defaultdict(int),
        "dod_counts": defaultdict(int),
        "effect_picks": defaultdict(int),
        "outcomes": defaultdict(int),
    })

    for r in rows:
        payload = _safe_json_load(r.data_json)
        team = per_team[r.team_key]
        team["participants"] += 1
        team["avg_initial"] += float(r.score_initial or 0)
        if r.score_improved is not None:
            team["improved"] += 1
            team["avg_improved"] += float(r.score_improved or 0)
        outcome = r.outcome_improved or r.outcome_initial
        if outcome:
            team["outcomes"][outcome] += 1
        source = payload.get("improved") or payload.get("initial") or {}
        for k in (source.get("dor") or []):
            team["dor_counts"][k] += 1
        for k in (source.get("dod") or []):
            team["dod_counts"][k] += 1
        for rk, effs in (source.get("mapping") or {}).items():
            for e in (effs or []):
                team["effect_picks"][e] += 1

    teams_view = []
    for t in content["teams"]:
        data = per_team.get(t["key"])
        if not data:
            teams_view.append({
                "key": t["key"], "title": t["title"], "participants": 0,
                "avg_initial": 0.0, "avg_improved": 0.0, "improved_count": 0,
                "dor_top": [], "dod_top": [], "effect_top": [],
                "outcomes": {},
            })
            continue
        avg_initial = data["avg_initial"] / data["participants"] if data["participants"] else 0.0
        avg_improved = data["avg_improved"] / data["improved"] if data["improved"] else 0.0
        dor_top = sorted(data["dor_counts"].items(), key=lambda x: -x[1])[:5]
        dod_top = sorted(data["dod_counts"].items(), key=lambda x: -x[1])[:5]
        effect_top = sorted(data["effect_picks"].items(), key=lambda x: -x[1])[:5]
        teams_view.append({
            "key": t["key"],
            "title": t["title"],
            "participants": data["participants"],
            "improved_count": data["improved"],
            "avg_initial": round(avg_initial, 1),
            "avg_improved": round(avg_improved, 1),
            "dor_top": [{"rule": k, "count": v} for k, v in dor_top],
            "dod_top": [{"rule": k, "count": v} for k, v in dod_top],
            "effect_top": [{"effect": k, "count": v} for k, v in effect_top],
            "outcomes": dict(data["outcomes"]),
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "total_participants": g.participants.count(),
        "total_answers": len(rows),
        "teams": teams_view,
    })


# --------------------------- facilitator ---------------------------


@bp_agile_dor_dod.get("/sessions/<int:session_id>/results")
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
        rows = AgileTrainingDorDodAnswer.query.filter_by(group_id=g.id).all()
        participants_count = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants_count
        totals["answers"] += len(rows)

        avg_initial = (
            sum(float(r.score_initial or 0) for r in rows) / len(rows)
            if rows else 0.0
        )
        improved_rows = [r for r in rows if r.score_improved is not None]
        avg_improved = (
            sum(float(r.score_improved or 0) for r in improved_rows) / len(improved_rows)
            if improved_rows else 0.0
        )
        # % «здоровых» исходов
        healthy = 0
        for r in rows:
            outcome = r.outcome_improved or r.outcome_initial
            if outcome in ("stable", "predictable"):
                healthy += 1
        health_pct = round(100 * healthy / len(rows)) if rows else 0

        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants_count,
            "answers_count": len(rows),
            "improved_count": len(improved_rows),
            "avg_initial": round(avg_initial, 1),
            "avg_improved": round(avg_improved, 1),
            "health_pct": health_pct,
        })

    leaderboard_best = sorted(groups_view, key=lambda x: (-x["health_pct"], -x["avg_improved"], x["id"]))
    leaderboard_growth = sorted(
        groups_view,
        key=lambda x: (-(x["avg_improved"] - x["avg_initial"]), x["id"]),
    )

    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "content": content,
        "totals": totals,
        "groups": groups_view,
        "leaderboard_best": leaderboard_best,
        "leaderboard_growth": leaderboard_growth,
    })


@bp_agile_dor_dod.get("/groups/<int:group_id>/results")
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

    rows = AgileTrainingDorDodAnswer.query.filter_by(group_id=g.id).all()
    per_team: Dict[str, Dict] = defaultdict(lambda: {
        "participants": 0,
        "dor_counts": defaultdict(int),
        "dod_counts": defaultdict(int),
        "effect_picks": defaultdict(int),
        "rule_in_dor": defaultdict(int),
        "rule_in_dod": defaultdict(int),
        "outcomes": defaultdict(int),
        "antipatterns": defaultdict(int),
        "avg_initial": 0.0,
        "avg_improved": 0.0,
        "improved": 0,
    })
    for r in rows:
        team = per_team[r.team_key]
        team["participants"] += 1
        team["avg_initial"] += float(r.score_initial or 0)
        if r.score_improved is not None:
            team["improved"] += 1
            team["avg_improved"] += float(r.score_improved or 0)
        outcome = r.outcome_improved or r.outcome_initial
        if outcome:
            team["outcomes"][outcome] += 1
        payload = _safe_json_load(r.data_json)
        source = payload.get("improved") or payload.get("initial") or {}
        for k in (source.get("dor") or []):
            team["dor_counts"][k] += 1
            team["rule_in_dor"][k] += 1
        for k in (source.get("dod") or []):
            team["dod_counts"][k] += 1
            team["rule_in_dod"][k] += 1
        for rk, effs in (source.get("mapping") or {}).items():
            for e in (effs or []):
                team["effect_picks"][e] += 1
        ev = payload.get("eval_improved") or payload.get("eval_initial") or {}
        for ap in (ev.get("antipatterns") or []):
            team["antipatterns"][ap] += 1

    teams_view = []
    for t in content["teams"]:
        d = per_team.get(t["key"])
        if not d:
            teams_view.append({
                "key": t["key"], "title": t["title"], "participants": 0,
                "avg_initial": 0.0, "avg_improved": 0.0, "improved_count": 0,
                "rules": [], "effect_picks": [], "outcomes": {}, "antipatterns": {},
            })
            continue
        total = d["participants"]
        rules_view = []
        for r in content["rules"]:
            in_dor = d["rule_in_dor"].get(r["key"], 0)
            in_dod = d["rule_in_dod"].get(r["key"], 0)
            rules_view.append({
                "key": r["key"],
                "title": r["title"],
                "expected_column": r["expected_column"],
                "dor_count": in_dor,
                "dod_count": in_dod,
                "dor_pct": round(100 * in_dor / total) if total else 0,
                "dod_pct": round(100 * in_dod / total) if total else 0,
            })
        effect_picks = []
        for e in content["effects"]:
            cnt = d["effect_picks"].get(e["key"], 0)
            effect_picks.append({
                "key": e["key"],
                "title": e["title"],
                "provocative": e["provocative"],
                "count": cnt,
                "pct": round(100 * cnt / total) if total else 0,
            })
        teams_view.append({
            "key": t["key"],
            "title": t["title"],
            "participants": total,
            "improved_count": d["improved"],
            "avg_initial": round(d["avg_initial"] / total, 1) if total else 0.0,
            "avg_improved": round(d["avg_improved"] / d["improved"], 1) if d["improved"] else 0.0,
            "rules": rules_view,
            "effect_picks": effect_picks,
            "outcomes": dict(d["outcomes"]),
            "antipatterns": dict(d["antipatterns"]),
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "teams": teams_view,
    })


@bp_agile_dor_dod.post("/groups/<int:group_id>/reset")
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
    AgileTrainingDorDodAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})


@bp_agile_dor_dod.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детали каждого участника: тип команды, обе итерации, антипаттерны."""
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
    rules_index = {r["key"]: r for r in content["rules"]}
    effects_index = {e["key"]: e for e in content["effects"]}
    teams_index = {t["key"]: t for t in content["teams"]}

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows_out = []
    for idx, p in enumerate(participants, start=1):
        a = AgileTrainingDorDodAnswer.query.filter_by(participant_id=p.id).first()
        if not a:
            rows_out.append({
                "id": p.id,
                "display_name": p.display_name or f"#{idx}",
                "anonymous_label": f"#{idx}",
                "joined_at": p.created_at.isoformat() if p.created_at else None,
                "has_answer": False,
            })
            continue
        payload = _safe_json_load(a.data_json)

        def _inflate_side(side: Optional[Dict]):
            if not side:
                return None
            dor = [
                {"key": k, "title": rules_index.get(k, {}).get("title", k),
                 "expected_column": rules_index.get(k, {}).get("expected_column", "either")}
                for k in (side.get("dor") or [])
            ]
            dod = [
                {"key": k, "title": rules_index.get(k, {}).get("title", k),
                 "expected_column": rules_index.get(k, {}).get("expected_column", "either")}
                for k in (side.get("dod") or [])
            ]
            mapping = {}
            for rk, effs in (side.get("mapping") or {}).items():
                mapping[rk] = [
                    {"key": e, "title": effects_index.get(e, {}).get("title", e),
                     "provocative": effects_index.get(e, {}).get("provocative", False)}
                    for e in (effs or [])
                ]
            return {"dor": dor, "dod": dod, "mapping": mapping}

        rows_out.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "has_answer": True,
            "team_key": a.team_key,
            "team_title": teams_index.get(a.team_key, {}).get("title", a.team_key),
            "score_initial": float(a.score_initial or 0),
            "score_improved": (float(a.score_improved) if a.score_improved is not None else None),
            "outcome_initial": a.outcome_initial,
            "outcome_improved": a.outcome_improved,
            "initial": _inflate_side(payload.get("initial")),
            "improved": _inflate_side(payload.get("improved")),
            "eval_initial": payload.get("eval_initial"),
            "eval_improved": payload.get("eval_improved"),
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows_out,
    })

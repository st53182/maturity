"""Backend для упражнения Cynefin в Agile Training.

Использует общие сущности сессии/группы/участника из `agile_training`
(session.exercise_key = "cynefin") и собственную таблицу ответов
`AgileTrainingCynefinAnswer`.

Публичные эндпоинты (для участников) не требуют авторизации и
идентифицируют человека по `participant_token`, полученному через
уже существующий эндпоинт `/api/agile-training/g/<slug>/participant`.

Фасилитаторские эндпоинты требуют JWT и проверяют, что сессия
принадлежит текущему пользователю.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingCynefinAnswer,
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingSession,
)
from cynefin_content import (
    CASES,
    DOMAIN_KEYS,
    STRATEGIES,
    get_case_debrief,
    get_cases_for_locale,
    get_strategies_for_locale,
    get_strategy_label,
    valid_case_keys,
    valid_domain_keys,
    valid_strategy_keys,
)


bp_agile_cynefin = Blueprint(
    "agile_cynefin", __name__, url_prefix="/api/agile-training/cynefin"
)


# --------------------------- helpers ---------------------------


def _uid() -> int:
    return int(get_jwt_identity())


def _resolve_locale(explicit: Optional[str], session: Optional[AgileTrainingSession]) -> str:
    lc = (explicit or "").strip().lower()
    if lc not in {"ru", "en"}:
        lc = (getattr(session, "locale", None) or "ru") if session else "ru"
    return lc if lc in {"ru", "en"} else "ru"


def _group_by_slug(slug: str) -> Optional[AgileTrainingGroup]:
    return AgileTrainingGroup.query.filter_by(slug=(slug or "").strip()).first()


def _session_for_owner(session_id: int, uid: int) -> Optional[AgileTrainingSession]:
    return AgileTrainingSession.query.filter_by(id=session_id, owner_user_id=uid).first()


def _aggregate_case_stats(group_id: int, case_key: str) -> Dict:
    """Статистика по одному кейсу в группе: распределение доменов и стратегий."""
    rows = (
        db.session.query(
            AgileTrainingCynefinAnswer.selected_domain,
            db.func.count(AgileTrainingCynefinAnswer.id),
        )
        .filter_by(group_id=group_id, case_key=case_key)
        .group_by(AgileTrainingCynefinAnswer.selected_domain)
        .all()
    )
    by_domain: Dict[str, int] = {dk: 0 for dk in DOMAIN_KEYS}
    total = 0
    for domain, cnt in rows:
        c = int(cnt)
        total += c
        if domain in by_domain:
            by_domain[domain] = c
        else:
            # на случай странного значения — кладём отдельно
            by_domain[domain] = by_domain.get(domain, 0) + c

    pct_by_domain = {
        dk: (round(100 * by_domain[dk] / total) if total else 0) for dk in by_domain
    }

    strat_rows = (
        db.session.query(
            AgileTrainingCynefinAnswer.selected_domain,
            AgileTrainingCynefinAnswer.selected_strategy,
            db.func.count(AgileTrainingCynefinAnswer.id),
        )
        .filter_by(group_id=group_id, case_key=case_key)
        .group_by(
            AgileTrainingCynefinAnswer.selected_domain,
            AgileTrainingCynefinAnswer.selected_strategy,
        )
        .all()
    )
    strategies_by_domain: Dict[str, Dict[str, int]] = defaultdict(dict)
    for domain, strat, cnt in strat_rows:
        if not strat:
            continue
        strategies_by_domain[domain or "other"][strat] = int(cnt)

    return {
        "total": total,
        "counts": by_domain,
        "percent": pct_by_domain,
        "strategies": strategies_by_domain,
    }


def _aggregate_group_all_cases(group_id: int) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for c in CASES:
        out[c["key"]] = _aggregate_case_stats(group_id, c["key"])
    return out


def _participant_answers_map(participant_id: int) -> Dict[str, Dict]:
    rows = AgileTrainingCynefinAnswer.query.filter_by(participant_id=participant_id).all()
    return {
        r.case_key: {
            "selected_domain": r.selected_domain,
            "selected_strategy": r.selected_strategy,
            "custom_strategy": r.custom_strategy,
        }
        for r in rows
    }


def _expert_map() -> Dict[str, str]:
    return {c["key"]: c["expert_domain"] for c in CASES}


# --------------------------- public content ---------------------------


@bp_agile_cynefin.get("/content")
def content_public():
    """Отдаёт кейсы и типовые стратегии для указанной локали.

    GET /content?locale=ru — по умолчанию отдаёт русскоязычную версию.
    """
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({
        "locale": locale,
        "domains": DOMAIN_KEYS,
        "cases": get_cases_for_locale(locale),
        "strategies": get_strategies_for_locale(locale),
    })


@bp_agile_cynefin.get("/cases/<case_key>/debrief")
def case_debrief(case_key: str):
    """Экспертный домен, объяснение и последствия по всем доменам.

    Возвращается отдельно от группы, чтобы можно было переиспользовать
    и в фасилитаторском отчёте, и у участника.
    """
    locale = _resolve_locale(request.args.get("locale"), None)
    debrief = get_case_debrief(case_key, locale)
    if not debrief:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(debrief)


# --------------------------- participant endpoints ---------------------------


@bp_agile_cynefin.get("/g/<slug>/state")
def participant_state(slug: str):
    """Состояние прохождения для участника: сколько кейсов сделано, свои ответы.

    Приходит с ?participant_token=... Если токена нет — отвечаем пустой картой
    ответов, клиент всё равно может начать с нуля.
    """
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
    return jsonify({
        "answered": answered,
        "total": len(CASES),
    })


@bp_agile_cynefin.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Сохраняет (upsert) ответ участника по кейсу.

    Body:
      participant_token: str (required)
      case_key:          str (required)
      selected_domain:   one of obvious/complicated/complex/chaotic (required)
      selected_strategy: str (optional) — ключ одной из типовых стратегий домена
      custom_strategy:   str (optional) — свободный текст, если участник вводит свой вариант

    В ответе возвращаем дебриф (экспертный домен, последствия по доменам)
    и актуальную статистику группы по этому кейсу.
    """
    group = _group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    data = request.get_json(silent=True) or {}
    token = (data.get("participant_token") or "").strip()
    case_key = (data.get("case_key") or "").strip()
    selected_domain = (data.get("selected_domain") or "").strip().lower()
    selected_strategy = (data.get("selected_strategy") or "").strip() or None
    custom_strategy = (data.get("custom_strategy") or "").strip()[:2000] or None

    if not token:
        return jsonify({"error": "participant_token required"}), 400
    if case_key not in valid_case_keys():
        return jsonify({"error": "Unknown case_key"}), 400
    if selected_domain not in valid_domain_keys():
        return jsonify({"error": "Unknown selected_domain"}), 400
    if selected_strategy and selected_strategy not in valid_strategy_keys(selected_domain):
        # Если ключ стратегии не совпадает со словарём — трактуем как свой вариант.
        custom_strategy = custom_strategy or selected_strategy
        selected_strategy = None

    participant = AgileTrainingParticipant.query.filter_by(
        participant_token=token, group_id=group.id
    ).first()
    if not participant:
        return jsonify({"error": "Participant not found in this group"}), 404

    # upsert по (participant, case_key)
    answer = AgileTrainingCynefinAnswer.query.filter_by(
        participant_id=participant.id, case_key=case_key
    ).first()
    if answer:
        answer.selected_domain = selected_domain
        answer.selected_strategy = selected_strategy
        answer.custom_strategy = custom_strategy
    else:
        answer = AgileTrainingCynefinAnswer(
            group_id=group.id,
            participant_id=participant.id,
            case_key=case_key,
            selected_domain=selected_domain,
            selected_strategy=selected_strategy,
            custom_strategy=custom_strategy,
        )
        db.session.add(answer)
    db.session.commit()

    session = AgileTrainingSession.query.get(group.session_id)
    locale = _resolve_locale(data.get("locale"), session)
    debrief = get_case_debrief(case_key, locale) or {}
    stats = _aggregate_case_stats(group.id, case_key)
    strategy_label = (
        get_strategy_label(selected_domain, selected_strategy, locale)
        if selected_strategy else None
    )

    return jsonify({
        "saved": True,
        "answer": {
            "case_key": case_key,
            "selected_domain": selected_domain,
            "selected_strategy": selected_strategy,
            "custom_strategy": custom_strategy,
            "strategy_label": strategy_label,
        },
        "debrief": debrief,
        "stats": stats,
    })


@bp_agile_cynefin.get("/g/<slug>/results")
def participant_results(slug: str):
    """Итоговые результаты группы: по каждому кейсу — распределение доменов,
    экспертный домен, совпадения/расхождения с экспертом, топ спорных.
    """
    group = _group_by_slug(slug)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    session = AgileTrainingSession.query.get(group.session_id)
    locale = _resolve_locale(request.args.get("locale"), session)
    token = (request.args.get("participant_token") or "").strip()

    my_answers: Dict[str, Dict] = {}
    if token:
        participant = AgileTrainingParticipant.query.filter_by(
            participant_token=token, group_id=group.id
        ).first()
        if participant:
            my_answers = _participant_answers_map(participant.id)

    expert_map = _expert_map()
    per_case: List[Dict] = []
    controversy_rows: List[Dict] = []
    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}

    for c in CASES:
        key = c["key"]
        stats = _aggregate_case_stats(group.id, key)
        expert_domain = expert_map[key]
        expert_pct = int(stats["percent"].get(expert_domain, 0) or 0)
        # «Разброс мнений» = 100 - max(share) среди непустых ответов;
        # чем ближе к равномерному распределению, тем выше controversy.
        percents = [v for v in stats["percent"].values() if v]
        controversy = (100 - max(percents)) if percents else 0

        my = my_answers.get(key, {})
        my_domain = my.get("selected_domain")
        matches_expert = (my_domain == expert_domain) if my_domain else None

        row = {
            "key": key,
            "order": cases_loc[key]["order"],
            "category": cases_loc[key]["category"],
            "title": cases_loc[key]["title"],
            "scenario": cases_loc[key]["scenario"],
            "expert_domain": expert_domain,
            "expert_pct": expert_pct,
            "stats": stats,
            "my_domain": my_domain,
            "my_strategy": my.get("selected_strategy"),
            "my_custom_strategy": my.get("custom_strategy"),
            "matches_expert": matches_expert,
            "controversy": controversy,
        }
        per_case.append(row)
        controversy_rows.append({
            "key": key,
            "title": cases_loc[key]["title"],
            "controversy": controversy,
            "total": stats["total"],
        })

    top_controversial = sorted(
        [r for r in controversy_rows if r["total"] > 0],
        key=lambda r: (-r["controversy"], -r["total"]),
    )[:3]

    # домен-лидер по всей сессии участника в этой группе
    overall_domain_counts: Dict[str, int] = {dk: 0 for dk in DOMAIN_KEYS}
    for r in per_case:
        for dk, cnt in r["stats"]["counts"].items():
            overall_domain_counts[dk] = overall_domain_counts.get(dk, 0) + int(cnt or 0)
    overall_total = sum(overall_domain_counts.values())
    overall_percent = {
        dk: (round(100 * overall_domain_counts[dk] / overall_total) if overall_total else 0)
        for dk in overall_domain_counts
    }

    expert_matches = sum(1 for r in per_case if r["matches_expert"] is True)
    my_answered = sum(1 for r in per_case if r["my_domain"])

    return jsonify({
        "group": {"id": group.id, "name": group.name, "slug": group.slug},
        "participants_count": group.participants.count(),
        "locale": locale,
        "per_case": per_case,
        "top_controversial": top_controversial,
        "overall_domain_counts": overall_domain_counts,
        "overall_domain_percent": overall_percent,
        "my": {
            "answered": my_answered,
            "matches_expert": expert_matches,
        },
    })


# --------------------------- facilitator endpoints ---------------------------


@bp_agile_cynefin.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    """Агрегат по всем группам сессии.

    Для каждого кейса считаем процент «Актуально» по каждому домену в каждой
    группе, находим самые спорные (максимальный разброс между группами)
    и самые единодушные.
    """
    uid = _uid()
    s = _session_for_owner(session_id, uid)
    if not s:
        return jsonify({"error": "Not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), s)
    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}
    expert_map = _expert_map()

    groups = s.groups.order_by(AgileTrainingGroup.id.asc()).all()

    groups_summary: List[Dict] = []
    per_case_by_group: Dict[str, Dict[int, Dict]] = defaultdict(dict)
    for g in groups:
        participants_count = g.participants.count()
        answers_count = AgileTrainingCynefinAnswer.query.filter_by(group_id=g.id).count()
        distinct_cases = (
            db.session.query(AgileTrainingCynefinAnswer.case_key)
            .filter_by(group_id=g.id)
            .distinct()
            .count()
        )
        if participants_count == 0:
            status = "not_started"
        elif distinct_cases >= len(CASES):
            status = "completed"
        else:
            status = "in_progress"
        groups_summary.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants": participants_count,
            "answers": answers_count,
            "cases_seen": distinct_cases,
            "status": status,
        })
        for c in CASES:
            per_case_by_group[c["key"]][g.id] = _aggregate_case_stats(g.id, c["key"])

    cross_cases: List[Dict] = []
    for c in CASES:
        key = c["key"]
        expert_domain = expert_map[key]
        per_group_rows: List[Dict] = []
        expert_pcts: List[int] = []
        total_answers = 0
        for g in groups:
            st = per_case_by_group[key][g.id]
            tot = int(st["total"] or 0)
            ep = int(st["percent"].get(expert_domain, 0) or 0) if tot else None
            per_group_rows.append({
                "group_id": g.id,
                "group_name": g.name,
                "total": tot,
                "percent_by_domain": st["percent"],
                "expert_pct": ep,
            })
            if tot:
                expert_pcts.append(ep or 0)
                total_answers += tot
        if expert_pcts:
            spread = max(expert_pcts) - min(expert_pcts)
            avg_expert = round(sum(expert_pcts) / len(expert_pcts))
        else:
            spread = 0
            avg_expert = 0
        cross_cases.append({
            "key": key,
            "title": cases_loc[key]["title"],
            "category": cases_loc[key]["category"],
            "expert_domain": expert_domain,
            "by_group": per_group_rows,
            "spread": spread,
            "avg_expert_pct": avg_expert,
            "total": total_answers,
            "groups_answered": len(expert_pcts),
        })

    most_split = sorted(
        [r for r in cross_cases if r["groups_answered"] >= 2],
        key=lambda r: (-r["spread"], -r["total"]),
    )[:5]
    most_aligned = sorted(
        [r for r in cross_cases if r["groups_answered"] >= 2],
        key=lambda r: (r["spread"], -r["total"]),
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
        "cross_cases": cross_cases,
        "most_split": most_split,
        "most_aligned": most_aligned,
        "totals": totals,
    })


@bp_agile_cynefin.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results_facilitator(group_id: int):
    """Детальные результаты одной группы (удобно открыть в модалке)."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404
    locale = _resolve_locale(request.args.get("locale"), AgileTrainingSession.query.get(g.session_id))
    cases_loc = {c["key"]: c for c in get_cases_for_locale(locale)}
    expert_map = _expert_map()
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
            "expert_domain": expert_map[key],
            "expert_rationale": debrief.get("expert_rationale", ""),
            "stats": stats,
        })
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "per_case": per_case,
    })


@bp_agile_cynefin.post("/groups/<int:group_id>/reset")
@jwt_required()
def group_reset(group_id: int):
    """Сбрасывает ответы и участников группы (только для Cynefin-ответов)."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404
    AgileTrainingCynefinAnswer.query.filter_by(group_id=g.id).delete()
    # участников оставляем — они могут переиграть; достаточно очистить ответы
    db.session.commit()
    return jsonify({"reset": True})


@bp_agile_cynefin.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детальные ответы каждого участника: какой домен и стратегию выбрал
    по каждому кейсу. Используется в панели фасилитатора для разбора."""
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
    locale = (sess.locale if sess else "ru") or "ru"
    cases = get_cases_for_locale(locale)
    cases_index = {c["key"]: c for c in cases}

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows = []
    for idx, p in enumerate(participants, start=1):
        answers = (
            AgileTrainingCynefinAnswer.query
            .filter_by(participant_id=p.id)
            .order_by(AgileTrainingCynefinAnswer.id.asc())
            .all()
        )
        per_case = []
        for a in answers:
            case = cases_index.get(a.case_key) or {}
            per_case.append({
                "case_key": a.case_key,
                "case_title": case.get("title", a.case_key),
                "case_category": case.get("category", ""),
                "expert_domain": case.get("expert_domain"),
                "selected_domain": a.selected_domain,
                "selected_strategy": a.selected_strategy,
                "selected_strategy_label": (
                    get_strategy_label(a.selected_domain, a.selected_strategy, locale)
                    if (a.selected_strategy and a.selected_domain) else None
                ),
                "custom_strategy": a.custom_strategy,
                "domain_match": bool(case.get("expert_domain") and a.selected_domain == case.get("expert_domain")),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
        rows.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "cases_answered": len(answers),
            "correct_domain_count": sum(1 for c in per_case if c["domain_match"]),
            "answers": per_case,
        })
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows,
    })

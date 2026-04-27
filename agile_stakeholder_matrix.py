"""Матрица стейкхолдеров: влияние × заинтересованность (3×3), обсуждение, последствия.

`exercise_key` сессии: stakeholder_matrix. Публичные эндпоинты: `/g/<slug>/...` с participant_token.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingSession,
    AgileTrainingStakeholderMatrixAnswer,
)

bp_agile_stakeholder_matrix = Blueprint(
    "agile_stakeholder_matrix", __name__, url_prefix="/api/agile-training/stakeholder-matrix"
)

AI_CALLS_LIMIT = 12
AI_PROMPT_LIMIT = 2000
ALLOWED_SCREENS = {
    "context", "roles", "matrix_r1", "discussion", "strategy",
    "consequences", "event", "matrix_r2", "final",
}
ROLE_IDS = [
    "cto", "cfo", "hr", "po", "developer", "marketing", "sponsor", "ciso",
    "pm", "customer", "end_user", "compliance",
]

EVENT_OPTIONS = {
    "delays", "resistance", "budget_up", "tech_issues",
}

CONTENT: Dict[str, Any] = {
    "ru": {
        "scenario_lead": (
            "Компания внедряет новый цифровой продукт (онлайн-сервис, CRM "
            "или портал для клиентов). Команда хочет успешно запустить и закрепить продукт на рынке."
        ),
        "goal": "Успешно запустить продукт: согласованность с бизнесом, безопасностью, бюджетом и ожиданиями пользователей.",
        "axis": {
            "x": "Заинтересованность в вопросе / актуальности",
            "y": "Влияние на продукт и решения",
        },
        "level_labels": ["Низкое", "Среднее", "Высокое"],
        "level_labels_x": ["Низкая", "Средняя", "Высокая"],
        "cell_strategy": {
            "minimal": "Минимальные усилия",
            "informed": "Поддержание уровня информированности",
            "satisfied": "Поддержание уровня удовлетворённости",
            "close": "Пристальное внимание (управление вовлечением)",
        },
        "strategy_quadrant_hints": {
            "hh": "Высокое влияние + высокая заинтересованность: как вовлекать и синхронизировать?",
            "hl": "Высокое влияние + низкая заинтересованность: как удерживать внимание?",
            "lh": "Низкое влияние + высокая заинтересованность: как использовать энергию и поддержку?",
            "ll": "Низкое влияние + низкая заинтересованность: куда смотреть и что мониторить?",
        },
        "event_labels": {
            "delays": "Проект столкнулся с задержками: сдвигаются сроки релизов и зависимости стейкхолдеров.",
            "resistance": "Сопротивление изменениям: люди боятся новых процессов и рисков.",
            "budget_up": "Рост бюджета: смета пересматривается, нужны согласования с финансами.",
            "tech_issues": "Технические сбои и интеграции: стабильность и безопасность в фокусе.",
        },
    },
    "en": {
        "scenario_lead": (
            "The company is rolling out a new digital product (an online service, CRM, or customer portal). "
            "The team wants a successful launch and stable adoption."
        ),
        "goal": "Launch successfully: align business, security, budget, and user expectations.",
        "axis": {
            "x": "Interest in the topic / relevance",
            "y": "Influence on the product and decisions",
        },
        "level_labels": ["Low", "Medium", "High"],
        "level_labels_x": ["Low", "Medium", "High"],
        "cell_strategy": {
            "minimal": "Minimal effort",
            "informed": "Keep informed",
            "satisfied": "Keep satisfied",
            "close": "Manage closely",
        },
        "strategy_quadrant_hints": {
            "hh": "High power + high interest: how to engage and stay aligned?",
            "hl": "High power + low interest: how to keep their attention?",
            "lh": "Low power + high interest: how to use energy and support?",
            "ll": "Low power + low interest: what to monitor and how often?",
        },
        "event_labels": {
            "delays": "The project hit delays: releases and hand-offs slip.",
            "resistance": "Change resistance: people fear new process and risk.",
            "budget_up": "Budget pressure: more approvals needed with finance.",
            "tech_issues": "Tech issues: reliability and security are in focus.",
        },
    },
}


# ------------------------- matrix logic (3x3) -------------------------


def cell_bucket(infl: int, interest: int) -> str:
    """infl, interest: 0=low, 1=mid, 2=high. Matches reference grid."""
    if infl == 0 and interest == 0:
        return "minimal"
    if infl == 0 and interest in (1, 2):
        return "informed"
    if infl == 2 and interest == 2:
        return "close"
    return "satisfied"


def compute_consequences(placements: Dict[str, Any], locale: str) -> List[str]:
    """Heuristic «последствия» без оценок «верно/неверно»."""
    msgs: List[str] = []

    valid: Dict[str, Tuple[int, int]] = {}
    for rid, pos in (placements or {}).items():
        if not pos or not isinstance(pos, dict):
            continue
        try:
            infl = int(pos.get("infl", -1))
            interest = int(pos.get("int", -1))
        except (TypeError, ValueError):
            continue
        if infl not in (0, 1, 2) or interest not in (0, 1, 2):
            continue
        valid[rid] = (infl, interest)

    if not valid:
        return []

    in_close = [r for r, (i, n) in valid.items() if i == 2 and n == 2]
    if len(in_close) > 4:
        if locale == "en":
            msgs.append("Many people land in 'manage closely': the team can burn out in coordination; clarify priorities and cadence.")
        else:
            msgs.append(
                "Много ролей в зоне «пристальное внимание»: риск перегруза встречами и согласованиями; стоит уточнить приоритеты и каденции."
            )

    # Role-specific *risks* when placed in low power / very corner cells (soft hints)
    def add_if(role: str, cond: bool, ru: str, en: str) -> None:
        if not cond:
            return
        msgs.append(en if locale == "en" else ru)

    for r, (infl, interest) in valid.items():
        s = infl + interest
        if r == "cfo" and s <= 1:
            add_if(
                r, True,
                "Если финансовый лидер остаётся в зоне низкого влияния/внимания — выше риск сюрпризов с бюджетом и согласований по списаниям.",
                "If finance stays in a low power / low attention cell, budget and approval surprises are more likely.",
            )
        if r == "cto" and infl < 1:
            add_if(
                r, True,
                "Если сильно недооценить влияние технического руководителя, позже всплывают риски архитектуры, интеграций и масштабирования.",
                "If technical leadership is placed with very low power, later risks include integration, architecture, and scale.",
            )
        if r == "ciso" and (infl < 1 or s <= 1):
            add_if(
                r, True,
                "Слабое вовлечение security при цифровом продукте усиливает риск инцидентов и срыва внешних требований (комплаенс, аудит).",
                "If security is under-involved, incident and compliance exposure grows.",
            )
        if r == "sponsor" and (infl < 2 and interest < 1):
            add_if(
                r, True,
                "Спонсор с невысокой заинтересованностью: решения о приоритете бюджета и защите инициативы сложнее защищать.",
                "A sponsor with low interest makes it harder to protect priority and budget.",
            )
        if r in ("customer", "end_user") and infl == 0 and interest == 0:
            add_if(
                r, True,
                "Пользователи/заказчики в клетке «минимальные усилия» — риск неверного продукта и слабой валидации гипотез.",
                "Users in 'minimal effort' can mean weak validation and product–market misfit.",
            )
        if r == "po" and s >= 4:
            add_if(
                r, True,
                "PO в зоне максимального внимания — логично, но убедитесь, что у роли остаётся время на бэклог и trade-off'ы, а не только встречи.",
                "PO in the highest-engagement corner is plausible — watch meeting load vs backlog and trade-offs.",
            )
    return msgs[:10]


# ------------------------- helpers -------------------------


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


def _group_and_session(slug: str):
    g = _group_by_slug(slug)
    if not g:
        return None, None
    sess = AgileTrainingSession.query.get(g.session_id)
    if sess and (getattr(sess, "exercise_key", None) or "") != "stakeholder_matrix":
        return None, None
    return g, sess


def _safe_json_load(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _clamp_text(value: Any, limit: int = 4000) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


def _require_participant(group: AgileTrainingGroup, token: str) -> Optional[AgileTrainingParticipant]:
    if not token:
        return None
    return (
        AgileTrainingParticipant.query
        .filter_by(group_id=group.id, participant_token=token)
        .first()
    )


def _get_or_create_answer(group_id: int, participant_id: int) -> AgileTrainingStakeholderMatrixAnswer:
    a = (
        AgileTrainingStakeholderMatrixAnswer.query
        .filter_by(participant_id=participant_id)
        .first()
    )
    if a:
        return a
    a = AgileTrainingStakeholderMatrixAnswer(
        group_id=group_id,
        participant_id=participant_id,
        data_json=json.dumps({}, ensure_ascii=False),
    )
    db.session.add(a)
    return a


def _default_data() -> Dict:
    return {
        "placements_r1": {},
        "placements_r2": {},
        "discussion": {},
        "strategy_quadrant": {"hh": "", "hl": "", "lh": "", "ll": ""},
        "event_key": None,
        "ai_history": [],
    }


def _serialize_answer(a: AgileTrainingStakeholderMatrixAnswer) -> Dict:
    data = _safe_json_load(a.data_json)
    for k in _default_data():
        if k not in data:
            data[k] = _default_data()[k] if k != "strategy_quadrant" else {"hh": "", "hl": "", "lh": "", "ll": ""}
    if "strategy_quadrant" not in data or not isinstance(data["strategy_quadrant"], dict):
        data["strategy_quadrant"] = {"hh": "", "hl": "", "lh": "", "ll": ""}
    for q in ("hh", "hl", "lh", "ll"):
        if q not in data["strategy_quadrant"]:
            data["strategy_quadrant"][q] = ""
    sc = a.screen or data.get("screen") or "context"
    if sc not in ALLOWED_SCREENS:
        sc = "context"
    return {
        "screen": sc,
        "placements_r1": data.get("placements_r1") or {},
        "placements_r2": data.get("placements_r2") or {},
        "discussion": data.get("discussion") or {},
        "strategy_quadrant": data["strategy_quadrant"],
        "event_key": data.get("event_key"),
        "ai_history": data.get("ai_history") or [],
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT - int(a.ai_calls or 0)),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _openai_client():
    try:
        from openai import OpenAI
    except Exception:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None


# ------------------------- public (participant) -------------------------


@bp_agile_stakeholder_matrix.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g or not sess:
        return jsonify({"error": "Group not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip()
    content = dict(CONTENT.get(locale, CONTENT["ru"]))
    content["role_ids"] = ROLE_IDS
    content["event_keys"] = list(EVENT_OPTIONS)

    answer_payload = None
    if token:
        p = _require_participant(g, token)
        if p:
            a = (
                AgileTrainingStakeholderMatrixAnswer.query
                .filter_by(participant_id=p.id)
                .first()
            )
            if a:
                answer_payload = _serialize_answer(a)
                c1 = compute_consequences(answer_payload.get("placements_r1") or {}, locale)
                c2 = compute_consequences(answer_payload.get("placements_r2") or {}, locale)
                answer_payload["consequence_hints_r1"] = c1
                answer_payload["consequence_hints_r2"] = c2

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "session": {
            "id": sess.id,
            "title": sess.title or "",
            "exercise_key": "stakeholder_matrix",
            "locale": sess.locale or "ru",
        },
        "effective_locale": locale,
        "content": content,
        "ai_calls_limit": AI_CALLS_LIMIT,
        "answer": answer_payload,
    })


@bp_agile_stakeholder_matrix.post("/g/<slug>/answer")
def participant_answer(slug: str):
    g, _sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    data = _safe_json_load(a.data_json)
    for k, v in _default_data().items():
        if k not in data:
            data[k] = v

    if "placements_r1" in body and isinstance(body.get("placements_r1"), dict):
        data["placements_r1"] = _clean_placements(body.get("placements_r1"))
    if "placements_r2" in body and isinstance(body.get("placements_r2"), dict):
        data["placements_r2"] = _clean_placements(body.get("placements_r2"))
    if "discussion" in body and isinstance(body.get("discussion"), dict):
        data["discussion"] = _clean_discussion(body.get("discussion"))
    if "strategy_quadrant" in body and isinstance(body.get("strategy_quadrant"), dict):
        sq = data.get("strategy_quadrant") or {}
        for key in ("hh", "hl", "lh", "ll"):
            if key in body["strategy_quadrant"]:
                t = _clamp_text(body["strategy_quadrant"].get(key), 2000)
                if t is None:
                    sq.pop(key, None)
                else:
                    sq[key] = t
        data["strategy_quadrant"] = sq
    if "event_key" in body:
        ek = body.get("event_key")
        if ek is None or ek == "":
            data["event_key"] = None
        else:
            ek = str(ek).strip()
            if ek in EVENT_OPTIONS:
                data["event_key"] = ek
    if "screen" in body:
        sc = (body.get("screen") or "").strip().lower()
        if sc in ALLOWED_SCREENS:
            a.screen = sc
            data["screen"] = sc
    if body.get("clear_ai_history"):
        data["ai_history"] = []

    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()
    return jsonify({"saved": True, "answer": _serialize_answer(a)})


def _clean_placements(raw: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    for rid, v in raw.items():
        rkey = str(rid).strip()[:32]
        if rkey not in ROLE_IDS:
            continue
        if v is None:
            out[rkey] = None
            continue
        if not isinstance(v, dict):
            continue
        try:
            infl = int(v.get("infl", -1))
            interest = int(v.get("int", -1))
        except (TypeError, ValueError):
            continue
        if infl in (0, 1, 2) and interest in (0, 1, 2):
            out[rkey] = {"infl": infl, "int": interest}
    return out


def _clean_discussion(raw: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    for rid, d in raw.items():
        rkey = str(rid).strip()[:32]
        if rkey not in ROLE_IDS:
            continue
        if not isinstance(d, dict):
            continue
        o: Dict[str, str] = {}
        for f in ("why_power", "why_interest", "if_ignore"):
            if f in d:
                t = _clamp_text(d.get(f), 2000)
                if t is not None:
                    o[f] = t
        if o:
            out[rkey] = o
    return out


# ------------------------- AI (Socratic) -------------------------


_SYSTEM_AI = {
    "ru": (
        "Ты — фасилитатор тренинга по стейкхолдерам. Пользователи новички, не только из IT. "
        "Запрещено выдавать «правильные ответы» и оценивать. Задавай 1–3 уточняющих вопроса, "
        "предлагай варианты углов зрения и критериев, помоги аргументировать. "
        "Короткие абзацы, дружелюбно, по-русски. Markdown. Не придумывай деталей сценария."
    ),
    "en": (
        "You facilitate stakeholder training. Learners are beginners, not only IT. "
        "Do NOT provide single correct answers or grade. Ask 1–3 clarifying questions, "
        "offer alternative lenses and criteria, help them reason. "
        "Short, friendly, English, Markdown. Do not invent scenario facts."
    ),
}


@bp_agile_stakeholder_matrix.post("/g/<slug>/ai-assist")
def participant_ai(slug: str):
    g, sess = _group_and_session(slug)
    if not g or not sess:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    mode = (body.get("mode") or "generic").strip().lower()
    locale = _resolve_locale(body.get("locale"), sess)
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT) or ""
    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    if int(a.ai_calls or 0) >= AI_CALLS_LIMIT:
        return jsonify({"error": "ai_limit_exceeded", "limit": AI_CALLS_LIMIT}), 429

    data = _safe_json_load(a.data_json)
    hist = data.get("ai_history") or []
    if not isinstance(hist, list):
        hist = []

    client = _openai_client()
    reply_text = ""
    model_used = None

    mode_hint = {
        "matrix": "The learner is placing stakeholders on a 3x3 power/interest matrix.",
        "discussion": "The learner is answering reflection questions after placing roles.",
        "strategy": "The learner is writing engagement strategies for power/interest quadrants.",
        "consequences": "The learner is reviewing consequence hints — help them think, not confirm.",
    }.get(mode, "General help for the stakeholder training.")

    if client:
        system = _SYSTEM_AI.get(locale, _SYSTEM_AI["en"])
        user = f"{mode_hint}\n\nUser wrote:\n{user_input}\n"
        try:
            r = client.chat.completions.create(
                model=os.getenv("STAKEHOLDER_MATRIX_AI_MODEL", "gpt-4.1-mini"),
                temperature=0.5,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            reply_text = (r.choices[0].message.content or "").strip()
            model_used = getattr(r, "model", None)
        except Exception as e:
            reply_text = f"({locale == 'en' and 'Service error' or 'Сервис временно недоступен'}) {e!s}"[:500]
    else:
        if locale == "en":
            reply_text = (
                "**A few questions to try**\n"
                "- What would change the stakeholder's power in *your* org?\n"
                "- What makes their interest go up or down in this product?\n"
                "- If you ignored them, what would break first: budget, law, users, or tech?"
            )
        else:
            reply_text = (
                "**Вопросы, которые можно обсудить в команде**\n"
                "- Что в вашей ситуации увеличивает влияние этой роли?\n"
                "- Когда у неё падает или растёт заинтересованность?\n"
                "- Что «сломается» раньше, если не разговаривать: деньги, риск, срок, люди снаружи?"
            )
        model_used = "scripted"

    a.ai_calls = int(a.ai_calls or 0) + 1
    entry = {
        "role": "assistant",
        "content": reply_text,
        "mode": mode,
        "model": model_used,
    }
    hist.append({
        "role": "user",
        "content": user_input,
        "mode": mode,
    })
    hist.append(entry)
    data["ai_history"] = hist[-40:]
    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT - int(a.ai_calls or 0)),
    })


# ------------------------- facilitator -------------------------


@bp_agile_stakeholder_matrix.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g or (g.session.exercise_key or "") != "stakeholder_matrix":
        return jsonify({"error": "Not found"}), 404

    parts = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows = []
    for i, p in enumerate(parts, start=1):
        a = (
            AgileTrainingStakeholderMatrixAnswer.query
            .filter_by(participant_id=p.id)
            .first()
        )
        if not a:
            rows.append({
                "id": p.id,
                "display_name": p.display_name or f"#{i}",
                "has_answer": False,
            })
            continue
        data = _serialize_answer(a)
        rows.append({
            "id": p.id,
            "display_name": p.display_name or f"#{i}",
            "has_answer": True,
            "screen": data.get("screen"),
            "placements_r1": data.get("placements_r1"),
            "placements_r2": data.get("placements_r2"),
            "event_key": data.get("event_key"),
            "updated_at": data.get("updated_at"),
        })
    return jsonify({"group": {"id": g.id, "name": g.name, "slug": g.slug}, "participants": rows})


@bp_agile_stakeholder_matrix.get("/groups/<int:group_id>/results")
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

    ans = AgileTrainingStakeholderMatrixAnswer.query.filter_by(group_id=g.id).all()
    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(ans),
    })


@bp_agile_stakeholder_matrix.post("/groups/<int:group_id>/reset")
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
    AgileTrainingStakeholderMatrixAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})

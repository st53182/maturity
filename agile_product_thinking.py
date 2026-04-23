"""Backend тренинга «Продуктовое мышление: User Story / Job Story / декомпозиция».

API под префиксом `/api/agile-training/product-thinking`.

Использует общие сущности обучающего каркаса:
  - AgileTrainingSession (exercise_key = "product_thinking")
  - AgileTrainingGroup
  - AgileTrainingParticipant

Ответы храним одной записью на участника (JSON в data_json). Акцент тренинга —
обучение через практику и обсуждение, а не автоматическая оценка, поэтому в
бэкенде нет никакой "правильности": только хранение артефактов и AI-помощник
(анонимный, с лимитом обращений на участника).
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import (
    AgileTrainingGroup,
    AgileTrainingParticipant,
    AgileTrainingProductThinkingAnswer,
    AgileTrainingSession,
)


bp_agile_product_thinking = Blueprint(
    "agile_product_thinking", __name__, url_prefix="/api/agile-training/product-thinking"
)


# --------------------------- constants / content ---------------------------


ALLOWED_TECHNIQUES = {"spidr", "seven_dim"}
AI_CALLS_LIMIT_PER_PARTICIPANT = 15
AI_PROMPT_LIMIT_CHARS = 2000

ALLOWED_STAGES = (
    "case_choice",
    "intro",
    "example",
    "user_story",
    "job_story",
    "compare",
    "epic",
    "decomposition_example",
    "decomposition",
    "technique",
    "improve",
    "summary",
)
STAGE_SET = set(ALLOWED_STAGES)

ALLOWED_CASE_KEYS = {"it", "event"}


CONTENT = {
    "ru": {
        "cases": [
            {
                "key": "it",
                "emoji": "💻",
                "label": "IT-кейс: онлайн-запись",
                "short": "Пример из мира IT. Попробуйте на кейсе «онлайн-запись на приём».",
                "title": "Клиенты хотят записываться на приём онлайн, не звоня",
                "context": [
                    "Сейчас клиенты тратят время на звонки",
                    "Операторы перегружены — всё время занята линия",
                    "Записи теряются или происходят с ошибками",
                ],
                "goal": "Компания хочет улучшить этот процесс",
                "hint": "Опишите решение так, чтобы команда могла его реализовать",
                "epic_summary": "Онлайн-запись на приём",
                "epic_why": (
                    "Это не одна маленькая задача, а целая история: нужен экран "
                    "выбора услуги, календарь, подтверждение, напоминание. "
                    "Всё сразу за один вечер не сделать — поэтому это эпик."
                ),
                "examples": {
                    "user_story": "Как клиент, я хочу записаться онлайн, чтобы не тратить время на звонки",
                    "job_story": "Когда мне нужно записаться, я хочу сделать это онлайн, чтобы быстро выбрать удобное время",
                    "note": "Один и тот же сценарий можно описать по-разному — это влияет на понимание задачи командой",
                },
                "decomposition_examples": [
                    {
                        "label": "Вариант 1 — по шагам клиента",
                        "subtitle": "Режем по пути пользователя: что он делает по очереди",
                        "items": [
                            "Выбрать услугу",
                            "Выбрать дату",
                            "Выбрать удобное время",
                            "Подтвердить запись",
                            "Получить напоминание",
                        ],
                    },
                    {
                        "label": "Вариант 2 — от минимального к полному",
                        "subtitle": "Режем по уровню готовности: сначала самое простое, потом добавляем",
                        "items": [
                            "MVP: форма «имя + телефон», администратор сам назначает время",
                            "+ выбор даты из календаря",
                            "+ выбор конкретного времени",
                            "+ автоматическое подтверждение",
                            "+ напоминание за день",
                        ],
                    },
                ],
                "good_task": "Добавить кнопку «Записаться» на главной странице",
                "bad_task": "Сделать систему онлайн-записи",
            },
            {
                "key": "event",
                "emoji": "🎉",
                "label": "Не-IT: организовать корпоратив",
                "short": "Пример не из IT. Возьмите кейс «организовать корпоратив на 30 человек».",
                "title": "Руководитель попросил организовать корпоратив команде из 30 человек",
                "context": [
                    "Праздник нужно провести через 3 недели",
                    "Бюджет ограничен — надо уложиться",
                    "У людей разные ожидания: кто-то хочет активности, кто-то — спокойно поговорить",
                ],
                "goal": "Команда должна остаться довольной и провести вечер вместе",
                "hint": "Опишите, каким должен быть корпоратив, чтобы коллеги поняли, что делать",
                "epic_summary": "Организовать корпоратив на 30 человек",
                "epic_why": (
                    "Тут сразу много движений: место, еда, программа, приглашения, "
                    "фотограф. Если браться за всё одновременно, легко утонуть — "
                    "поэтому это эпик, его надо разбить на шаги."
                ),
                "examples": {
                    "user_story": "Как участник команды, я хочу прийти на корпоратив и хорошо отдохнуть, чтобы зарядиться перед новым кварталом",
                    "job_story": "Когда я получаю приглашение на корпоратив, я хочу быстро понять где, во сколько и что надевать, чтобы спокойно запланировать вечер",
                    "note": "Кейсы без IT тоже полезно описывать через User Story и Job Story — это помогает договориться с коллегами",
                },
                "decomposition_examples": [
                    {
                        "label": "Вариант 1 — по шагам подготовки",
                        "subtitle": "Режем по этапам: от выбора даты до самого праздника",
                        "items": [
                            "Выбрать дату",
                            "Найти подходящее место",
                            "Составить меню",
                            "Разослать приглашения",
                            "Продумать программу вечера",
                            "В день X — провести корпоратив",
                        ],
                    },
                    {
                        "label": "Вариант 2 — от простого к полному",
                        "subtitle": "Режем по «богатству» праздника: сначала простой минимум, потом украшаем",
                        "items": [
                            "Минимум: просто собраться в кафе после работы",
                            "+ заранее согласованное меню",
                            "+ программа с играми или ведущим",
                            "+ фотограф и оформление зала",
                            "+ подарки и сюрпризы для команды",
                        ],
                    },
                ],
                "good_task": "Позвонить в 3 кафе и узнать цену на 30 человек",
                "bad_task": "Организовать корпоратив",
            },
        ],
        "primer": {
            "epic_title": "Что такое «эпик»?",
            "epic_text": (
                "Эпик — это большая задача. Её нельзя сделать за один день, "
                "потому что внутри много маленьких шагов. Когда мы «декомпозируем», "
                "мы режем эпик на эти маленькие шаги, которые команда сможет делать по очереди."
            ),
            "decomposition_title": "Что такое «декомпозиция»?",
            "decomposition_text": (
                "Декомпозиция — это разделить одну большую цель на маленькие задачи. "
                "Хорошая маленькая задача — та, которую понятно, как сделать, и "
                "можно проверить отдельно. Плохая — это ещё целый проект, просто с новым словом."
            ),
            "good_task_label": "Так выглядит маленькая задача — её видно, что делать",
            "bad_task_label": "А это ещё не задача, а целый эпик — его надо резать дальше",
            "start_small_hint": (
                "Не пытайтесь описать всё идеально. Начните с 3–5 задач — каждую "
                "можно уточнить или разбить позже. Смело копируйте и меняйте примеры выше."
            ),
        },
        "techniques": {
            "spidr": {
                "title": "SPIDR (упрощённо)",
                "items": [
                    "разные сценарии",
                    "разные пользователи",
                    "разные данные",
                    "разные правила",
                ],
            },
            "seven_dim": {
                "title": "7 dimensions",
                "items": [
                    "разные кейсы",
                    "разные уровни сложности",
                    "разные ограничения",
                ],
            },
        },
    },
    "en": {
        "cases": [
            {
                "key": "it",
                "emoji": "💻",
                "label": "IT case: online booking",
                "short": "A case from the IT world. Try the «online appointment booking» scenario.",
                "title": "Customers want to book appointments online without calling",
                "context": [
                    "Customers spend time calling in",
                    "Operators are overloaded — the phone line is always busy",
                    "Bookings get lost or recorded with errors",
                ],
                "goal": "The company wants to improve this process",
                "hint": "Describe the solution so that the team can implement it",
                "epic_summary": "Online appointment booking",
                "epic_why": (
                    "This isn't a single small task, it's a whole story: a service "
                    "picker, a calendar, confirmation, a reminder. You can't build "
                    "it all in one evening — that's why it's an epic."
                ),
                "examples": {
                    "user_story": "As a customer, I want to book online, so I don't waste time on phone calls",
                    "job_story": "When I need to book, I want to do it online, so I can quickly pick a convenient time",
                    "note": "The same scenario can be described differently — and that shapes how the team understands the task",
                },
                "decomposition_examples": [
                    {
                        "label": "Option 1 — along the customer journey",
                        "subtitle": "Slice by user path: what the customer does step by step",
                        "items": [
                            "Pick a service",
                            "Pick a date",
                            "Pick a convenient time",
                            "Confirm the booking",
                            "Receive a reminder",
                        ],
                    },
                    {
                        "label": "Option 2 — from minimum to full",
                        "subtitle": "Slice by richness: start with the simplest thing, then grow it",
                        "items": [
                            "MVP: name + phone form, the admin assigns the time manually",
                            "+ pick the date from a calendar",
                            "+ pick a specific time",
                            "+ automatic confirmation",
                            "+ reminder the day before",
                        ],
                    },
                ],
                "good_task": "Add a «Book now» button on the home page",
                "bad_task": "Build the online booking system",
            },
            {
                "key": "event",
                "emoji": "🎉",
                "label": "Non-IT: organize a team party",
                "short": "A non-IT case. Try «organize a team party for 30 people».",
                "title": "Your manager asked you to organize a team party for 30 people",
                "context": [
                    "The party must happen in 3 weeks",
                    "The budget is limited — you must fit in",
                    "People have different expectations: some want activities, some want to chat",
                ],
                "goal": "The team should feel great and enjoy the evening together",
                "hint": "Describe what this party should be like so your colleagues know what to do",
                "epic_summary": "Organize a team party for 30 people",
                "epic_why": (
                    "There's a lot going on here: venue, food, programme, invitations, "
                    "a photographer. If you grab it all at once, you drown — that's why "
                    "it's an epic and needs to be broken down."
                ),
                "examples": {
                    "user_story": "As a team member, I want to come to the party and genuinely rest, so that I feel energized for the new quarter",
                    "job_story": "When I receive the invite, I want to quickly see where, when, and what to wear, so that I can plan my evening calmly",
                    "note": "Non-IT cases also benefit from User Story / Job Story — it helps you align with colleagues",
                },
                "decomposition_examples": [
                    {
                        "label": "Option 1 — along the preparation steps",
                        "subtitle": "Slice by phases: from picking the date to the day itself",
                        "items": [
                            "Pick the date",
                            "Find a suitable venue",
                            "Plan the menu",
                            "Send out invitations",
                            "Plan the evening's programme",
                            "Day X — run the party",
                        ],
                    },
                    {
                        "label": "Option 2 — from simple to rich",
                        "subtitle": "Slice by how elaborate the party is: start small, then decorate",
                        "items": [
                            "Minimum: just gather in a café after work",
                            "+ pre-agreed menu",
                            "+ programme with games or a host",
                            "+ photographer and venue decoration",
                            "+ gifts and surprises for the team",
                        ],
                    },
                ],
                "good_task": "Call 3 cafés and ask for the price for 30 people",
                "bad_task": "Organize the party",
            },
        ],
        "primer": {
            "epic_title": "What is an «epic»?",
            "epic_text": (
                "An epic is a big task. You can't finish it in a day because it "
                "contains many small steps. When we «decompose», we slice the epic "
                "into those small steps so the team can tackle them one by one."
            ),
            "decomposition_title": "What is «decomposition»?",
            "decomposition_text": (
                "Decomposition is splitting one big goal into small tasks. A good "
                "small task is one you clearly know how to do and can verify on its "
                "own. A bad one is still a whole project in disguise."
            ),
            "good_task_label": "This looks like a small task — you can tell what to do",
            "bad_task_label": "This is still an epic — it needs more splitting",
            "start_small_hint": (
                "Don't try to be perfect. Start with 3–5 tasks — you can refine or "
                "split them later. Feel free to copy and adapt the examples above."
            ),
        },
        "techniques": {
            "spidr": {
                "title": "SPIDR (simplified)",
                "items": [
                    "different paths",
                    "different users",
                    "different data",
                    "different rules",
                ],
            },
            "seven_dim": {
                "title": "7 dimensions",
                "items": [
                    "different cases",
                    "different complexity",
                    "different constraints",
                ],
            },
        },
    },
}


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


def _safe_json_load(raw: Optional[str]) -> Dict:
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _clamp_text(value, limit: int = 1200) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s[:limit]


def _clean_tasks(raw: Optional[List]) -> List[Dict]:
    out: List[Dict] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw[:30]):
        title = ""
        note = ""
        if isinstance(item, str):
            title = item
        elif isinstance(item, dict):
            title = str(item.get("title") or item.get("text") or "")
            note = str(item.get("note") or "")
        title = title.strip()[:240]
        note = note.strip()[:400]
        if not title:
            continue
        out.append({"id": f"t{idx+1}", "title": title, "note": note or None})
    return out


def _group_and_session(slug: str):
    g = _group_by_slug(slug)
    if not g:
        return None, None
    sess = AgileTrainingSession.query.get(g.session_id)
    return g, sess


def _require_participant(group: AgileTrainingGroup, token: str) -> Optional[AgileTrainingParticipant]:
    if not token:
        return None
    return (
        AgileTrainingParticipant.query
        .filter_by(group_id=group.id, participant_token=token)
        .first()
    )


def _get_or_create_answer(group_id: int, participant_id: int) -> AgileTrainingProductThinkingAnswer:
    a = (
        AgileTrainingProductThinkingAnswer.query
        .filter_by(participant_id=participant_id)
        .first()
    )
    if a:
        return a
    a = AgileTrainingProductThinkingAnswer(
        group_id=group_id,
        participant_id=participant_id,
        data_json=json.dumps({}, ensure_ascii=False),
    )
    db.session.add(a)
    return a


def _serialize_answer(a: AgileTrainingProductThinkingAnswer) -> Dict:
    data = _safe_json_load(a.data_json)
    case_key = data.get("case_key")
    if case_key not in ALLOWED_CASE_KEYS:
        case_key = None
    return {
        "stage": a.stage,
        "case_key": case_key,
        "user_story": a.user_story,
        "job_story": a.job_story,
        "chosen_technique": a.chosen_technique,
        "tasks": data.get("tasks") or [],
        "improved_tasks": data.get("improved_tasks") or [],
        "notes": data.get("notes") or {},
        "ai_history": data.get("ai_history") or [],
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


# --------------------------- public (participant) ---------------------------


@bp_agile_product_thinking.get("/content")
def content_public():
    locale = _resolve_locale(request.args.get("locale"), None)
    return jsonify({"locale": locale, **CONTENT.get(locale, CONTENT["ru"])})


@bp_agile_product_thinking.get("/g/<slug>/state")
def participant_state(slug: str):
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    locale = _resolve_locale(request.args.get("locale"), sess)
    token = (request.args.get("participant_token") or "").strip()
    answer_payload: Optional[Dict] = None
    if token:
        p = _require_participant(g, token)
        if p:
            a = (
                AgileTrainingProductThinkingAnswer.query
                .filter_by(participant_id=p.id)
                .first()
            )
            if a:
                answer_payload = _serialize_answer(a)

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "session": {
            "id": sess.id if sess else None,
            "title": sess.title if sess else "",
            "exercise_key": sess.exercise_key if sess else "product_thinking",
            "locale": sess.locale if sess else "ru",
        },
        "effective_locale": locale,
        "content": CONTENT.get(locale, CONTENT["ru"]),
        "ai_calls_limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
        "answer": answer_payload,
    })


@bp_agile_product_thinking.post("/g/<slug>/answer")
def participant_answer(slug: str):
    """Upsert всего артефакта участника.

    body:
      {
        "participant_token": "...",
        "stage": "user_story" | ...,
        "user_story": "...",
        "job_story": "...",
        "tasks": [{"title": ".."}, ...],
        "improved_tasks": [...],
        "chosen_technique": "spidr" | "seven_dim" | null,
        "notes": {"intro": "...", "compare": "..."},
        "clear_ai_history": bool
      }
    """
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

    if "case_key" in body:
        ck = body.get("case_key")
        if ck is None or ck == "":
            data.pop("case_key", None)
        else:
            ck = str(ck).strip().lower()
            if ck in ALLOWED_CASE_KEYS:
                data["case_key"] = ck
    if "user_story" in body:
        a.user_story = _clamp_text(body.get("user_story"))
    if "job_story" in body:
        a.job_story = _clamp_text(body.get("job_story"))
    if "stage" in body:
        stg = (body.get("stage") or "").strip().lower()
        a.stage = stg if stg in STAGE_SET else a.stage
    if "chosen_technique" in body:
        tech = body.get("chosen_technique")
        if tech is None or tech == "":
            a.chosen_technique = None
        elif str(tech).strip().lower() in ALLOWED_TECHNIQUES:
            a.chosen_technique = str(tech).strip().lower()
    if "tasks" in body:
        cleaned = _clean_tasks(body.get("tasks"))
        data["tasks"] = cleaned
        a.tasks_count = len(cleaned)
    if "improved_tasks" in body:
        data["improved_tasks"] = _clean_tasks(body.get("improved_tasks"))
    if "notes" in body and isinstance(body.get("notes"), dict):
        notes_in = body.get("notes") or {}
        notes_current = data.get("notes") or {}
        if not isinstance(notes_current, dict):
            notes_current = {}
        for k, v in notes_in.items():
            if not isinstance(k, str):
                continue
            key = k.strip()[:32]
            if not key:
                continue
            txt = _clamp_text(v, 2000)
            if txt is None:
                notes_current.pop(key, None)
            else:
                notes_current[key] = txt
        data["notes"] = notes_current
    if body.get("clear_ai_history"):
        data["ai_history"] = []

    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({"saved": True, "answer": _serialize_answer(a)})


# --------------------------- AI helper (anonymous, limited per participant) ---------------------------


def _openai_client():
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None


_SYSTEM_PROMPTS = {
    "ru": (
        "Ты — доброжелательный фасилитатор тренинга по продуктовому мышлению. "
        "Ученики — новички, не обязательно из IT. Никогда не говори «правильно/неправильно» "
        "и не выставляй оценок. Вместо этого задавай 1–3 коротких уточняющих вопроса, "
        "предложи вариант формулировки и коротко объясни, что можно улучшить. "
        "Пиши кратко, дружелюбно, по-русски, без жаргона. Отвечай в Markdown: "
        "короткие абзацы, списки, **жирный** для акцентов. Не придумывай факты о кейсе."
    ),
    "en": (
        "You are a friendly facilitator for a product-thinking training. "
        "Learners are beginners, not necessarily from IT. Never say 'correct/incorrect' "
        "and never grade. Instead ask 1-3 short clarifying questions, suggest a wording, "
        "and briefly explain what could be improved. Keep it short and friendly, in English, "
        "no jargon. Reply in Markdown: short paragraphs, lists, **bold** for emphasis. "
        "Do not invent facts about the case."
    ),
}


def _ai_mode_instruction(mode: str, locale: str) -> str:
    mode = (mode or "").strip().lower()
    if locale == "en":
        table = {
            "user_story": "The learner writes a User Story in the format \"As a [who], I want [what], so that [why]\". Ask about the user, need and value; suggest a clean User Story and note what could be clearer.",
            "job_story": "The learner writes a Job Story in the format \"When [situation], I want [motivation], so that [outcome]\". Help them reword it and briefly explain the difference from a User Story.",
            "decomposition": "The learner splits a solution into tasks. For each task ask: can it be done quickly? does it have standalone value? can it be tested? Suggest how to split items that look too big.",
            "improve": "The learner is improving their decomposition. Suggest new slices using SPIDR or 7 dimensions, and point to items that could still be split further.",
            "generic": "Help the learner move on. Ask 1-2 clarifying questions and suggest the next step.",
        }
    else:
        table = {
            "user_story": "Ученик пишет User Story в формате «Как [кто], я хочу [что], чтобы [зачем]». Задай вопросы про пользователя, потребность и ценность, предложи аккуратную User Story и отметь, что можно сделать яснее.",
            "job_story": "Ученик пишет Job Story в формате «Когда [ситуация], я хочу [мотивация], чтобы [результат]». Помоги переформулировать и коротко объясни разницу с User Story.",
            "decomposition": "Ученик разбивает решение на задачи. По каждой задаче спрашивай: можно ли сделать быстро? есть ли ценность отдельно? можно ли протестировать? Предложи, как разбить слишком крупные задачи.",
            "improve": "Ученик дорабатывает декомпозицию. Предложи новые срезы по SPIDR или 7 dimensions, укажи, где можно разбить ещё.",
            "generic": "Помоги ученику двигаться дальше. Задай 1–2 уточняющих вопроса и предложи следующий шаг.",
        }
    return table.get(mode, table["generic"])


def _scripted_assist(mode: str, locale: str, user_input: str) -> str:
    """Fallback без OpenAI: заготовленные наводящие вопросы."""
    mode = (mode or "").strip().lower()
    if locale == "en":
        bank = {
            "user_story": (
                "**Questions to think about**\n\n"
                "- Who is the user? Be specific: a new customer? a regular customer?\n"
                "- What exactly do they want to do?\n"
                "- Why is it important to them right now?\n\n"
                "**Try the template**: _As a [who], I want [what], so that [why]._\n\n"
                "_Example_: As a customer, I want to book online, so I don't waste time on phone calls."
            ),
            "job_story": (
                "**Questions to think about**\n\n"
                "- When does this happen? What is the situation?\n"
                "- What is the person trying to achieve?\n"
                "- What outcome do they want?\n\n"
                "**Template**: _When [situation], I want [motivation], so that [outcome]._"
            ),
            "decomposition": (
                "**Questions per task**\n\n"
                "- Can it be done quickly?\n"
                "- Does it bring value on its own?\n"
                "- Can it be tested?\n\n"
                "If a task feels too big, try splitting by data, rules, or user types."
            ),
            "improve": (
                "**Ideas to refine**\n\n"
                "- SPIDR: split by different paths, users, data, rules.\n"
                "- 7 dimensions: different cases, different complexity, different constraints.\n\n"
                "Pick one task and try two different ways to split it."
            ),
            "generic": "Take a breath. What is the very next thing a team would need to start working on?",
        }
    else:
        bank = {
            "user_story": (
                "**Подумайте над вопросами**\n\n"
                "- Кто пользователь? Будьте конкретны: новый клиент? постоянный?\n"
                "- Что именно он хочет сделать?\n"
                "- Почему это важно прямо сейчас?\n\n"
                "**Попробуйте шаблон**: _Как [кто], я хочу [что], чтобы [зачем]._\n\n"
                "_Пример_: Как клиент, я хочу записаться онлайн, чтобы не тратить время на звонки."
            ),
            "job_story": (
                "**Вопросы для размышления**\n\n"
                "- Когда это происходит? В какой ситуации?\n"
                "- Что человек пытается сделать?\n"
                "- Какой результат он хочет получить?\n\n"
                "**Шаблон**: _Когда [ситуация], я хочу [мотивация], чтобы [результат]._"
            ),
            "decomposition": (
                "**Вопросы по каждой задаче**\n\n"
                "- Можно ли сделать быстро?\n"
                "- Есть ли ценность отдельно?\n"
                "- Можно ли протестировать?\n\n"
                "Если задача выглядит слишком большой — попробуйте разбить по данным, правилам или типам пользователей."
            ),
            "improve": (
                "**Идеи для доработки**\n\n"
                "- SPIDR: разные сценарии, пользователи, данные, правила.\n"
                "- 7 dimensions: разные кейсы, уровни сложности, ограничения.\n\n"
                "Выберите одну задачу и попробуйте разбить её двумя разными способами."
            ),
            "generic": "Сделайте паузу. Что самое первое, с чего команде было бы удобно начать?",
        }
    return bank.get(mode, bank["generic"])


@bp_agile_product_thinking.post("/g/<slug>/ai-assist")
def participant_ai_assist(slug: str):
    """Анонимный AI-помощник. Лимит — AI_CALLS_LIMIT_PER_PARTICIPANT на участника.

    body:
      {
        "participant_token": "...",
        "mode": "user_story" | "job_story" | "decomposition" | "improve" | "generic",
        "user_input": "то, что человек пока написал",
        "locale": "ru" | "en"
      }
    """
    g, sess = _group_and_session(slug)
    if not g:
        return jsonify({"error": "Group not found"}), 404

    body = request.get_json(silent=True) or {}
    token = (body.get("participant_token") or "").strip()
    mode = (body.get("mode") or "generic").strip().lower()
    locale = _resolve_locale(body.get("locale"), sess)
    user_input = _clamp_text(body.get("user_input"), AI_PROMPT_LIMIT_CHARS) or ""

    if not token:
        return jsonify({"error": "participant_token required"}), 400

    p = _require_participant(g, token)
    if not p:
        return jsonify({"error": "Participant not found"}), 404

    a = _get_or_create_answer(g.id, p.id)
    if int(a.ai_calls or 0) >= AI_CALLS_LIMIT_PER_PARTICIPANT:
        return jsonify({
            "error": "ai_limit_exceeded",
            "limit": AI_CALLS_LIMIT_PER_PARTICIPANT,
            "ai_calls": int(a.ai_calls or 0),
        }), 429

    client = _openai_client()
    reply_text = ""
    model_used = None
    stored = _safe_json_load(a.data_json)
    chosen_case_key = stored.get("case_key")
    locale_content = CONTENT.get(locale, CONTENT["ru"])
    cases_list = locale_content.get("cases") or []
    case = None
    if chosen_case_key:
        case = next((c for c in cases_list if c.get("key") == chosen_case_key), None)
    if case is None and cases_list:
        case = cases_list[0]
    if client:
        system = _SYSTEM_PROMPTS.get(locale, _SYSTEM_PROMPTS["ru"])
        instruction = _ai_mode_instruction(mode, locale)
        if case:
            case_summary = f"{case['title']}. {' '.join(case.get('context') or [])} {case.get('goal') or ''}".strip()
        else:
            case_summary = ""
        user_msg = (
            f"{instruction}\n\n"
            f"Контекст кейса: {case_summary}\n\n"
            f"Что написал участник:\n{user_input or '(пусто)'}"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.5,
                max_tokens=500,
            )
            choice = resp.choices[0] if resp.choices else None
            if choice and getattr(choice, "message", None):
                reply_text = (choice.message.content or "").strip()
            model_used = getattr(resp, "model", None)
        except Exception as exc:
            reply_text = ""
            model_used = f"error:{type(exc).__name__}"

    if not reply_text:
        reply_text = _scripted_assist(mode, locale, user_input)
        model_used = model_used or "scripted"

    # Обновляем счётчик и историю
    a.ai_calls = int(a.ai_calls or 0) + 1
    data = _safe_json_load(a.data_json)
    history = data.get("ai_history") or []
    if not isinstance(history, list):
        history = []
    history.append({
        "mode": mode,
        "input": user_input,
        "reply": reply_text,
        "model": model_used,
    })
    data["ai_history"] = history[-20:]  # не раздуваем JSON
    a.data_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "model": model_used,
        "ai_calls": int(a.ai_calls or 0),
        "ai_calls_remaining": max(0, AI_CALLS_LIMIT_PER_PARTICIPANT - int(a.ai_calls or 0)),
    })


# --------------------------- facilitator ---------------------------


@bp_agile_product_thinking.get("/groups/<int:group_id>/participants")
@jwt_required()
def group_participants(group_id: int):
    """Детали каждого участника: User Story / Job Story / задачи."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    participants = (
        AgileTrainingParticipant.query
        .filter_by(group_id=g.id)
        .order_by(AgileTrainingParticipant.id.asc())
        .all()
    )
    rows: List[Dict] = []
    for idx, p in enumerate(participants, start=1):
        a = (
            AgileTrainingProductThinkingAnswer.query
            .filter_by(participant_id=p.id)
            .first()
        )
        if not a:
            rows.append({
                "id": p.id,
                "display_name": p.display_name or f"#{idx}",
                "anonymous_label": f"#{idx}",
                "joined_at": p.created_at.isoformat() if p.created_at else None,
                "has_answer": False,
            })
            continue
        data = _safe_json_load(a.data_json)
        rows.append({
            "id": p.id,
            "display_name": p.display_name or f"#{idx}",
            "anonymous_label": f"#{idx}",
            "joined_at": p.created_at.isoformat() if p.created_at else None,
            "has_answer": True,
            "stage": a.stage,
            "user_story": a.user_story,
            "job_story": a.job_story,
            "chosen_technique": a.chosen_technique,
            "tasks": data.get("tasks") or [],
            "improved_tasks": data.get("improved_tasks") or [],
            "notes": data.get("notes") or {},
            "ai_calls": int(a.ai_calls or 0),
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants": rows,
    })


@bp_agile_product_thinking.get("/groups/<int:group_id>/results")
@jwt_required()
def group_results(group_id: int):
    """Сводка по группе — сколько участников, сколько историй, техники."""
    uid = _uid()
    g = (
        AgileTrainingGroup.query
        .join(AgileTrainingSession, AgileTrainingSession.id == AgileTrainingGroup.session_id)
        .filter(AgileTrainingGroup.id == group_id, AgileTrainingSession.owner_user_id == uid)
        .first()
    )
    if not g:
        return jsonify({"error": "Not found"}), 404

    rows = AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).all()

    tech_counter: Counter = Counter()
    total_tasks = 0
    total_improved = 0
    user_story_count = 0
    job_story_count = 0
    with_any = 0
    stage_counter: Counter = Counter()
    for r in rows:
        if r.user_story:
            user_story_count += 1
        if r.job_story:
            job_story_count += 1
        if r.user_story or r.job_story:
            with_any += 1
        if r.chosen_technique:
            tech_counter[r.chosen_technique] += 1
        if r.stage:
            stage_counter[r.stage] += 1
        data = _safe_json_load(r.data_json)
        total_tasks += len(data.get("tasks") or [])
        total_improved += len(data.get("improved_tasks") or [])

    return jsonify({
        "group": {"id": g.id, "name": g.name, "slug": g.slug},
        "participants_count": g.participants.count(),
        "answers_count": len(rows),
        "user_story_count": user_story_count,
        "job_story_count": job_story_count,
        "with_any_count": with_any,
        "techniques": dict(tech_counter),
        "stages": dict(stage_counter),
        "avg_tasks": round(total_tasks / len(rows), 1) if rows else 0.0,
        "avg_improved_tasks": round(total_improved / len(rows), 1) if rows else 0.0,
    })


@bp_agile_product_thinking.get("/sessions/<int:session_id>/results")
@jwt_required()
def sessions_results(session_id: int):
    uid = _uid()
    sess = (
        AgileTrainingSession.query
        .filter_by(id=session_id, owner_user_id=uid)
        .first()
    )
    if not sess:
        return jsonify({"error": "Not found"}), 404

    groups = sess.groups.order_by(AgileTrainingGroup.id.asc()).all()
    groups_view: List[Dict] = []
    totals = {"groups": 0, "participants": 0, "answers": 0, "user_story": 0, "job_story": 0}
    techniques: Counter = Counter()
    for g in groups:
        rows = AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).all()
        participants_count = g.participants.count()
        totals["groups"] += 1
        totals["participants"] += participants_count
        totals["answers"] += len(rows)
        user_story_count = 0
        job_story_count = 0
        for r in rows:
            if r.user_story:
                user_story_count += 1
                totals["user_story"] += 1
            if r.job_story:
                job_story_count += 1
                totals["job_story"] += 1
            if r.chosen_technique:
                techniques[r.chosen_technique] += 1
        groups_view.append({
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "participants_count": participants_count,
            "answers_count": len(rows),
            "user_story_count": user_story_count,
            "job_story_count": job_story_count,
        })
    return jsonify({
        "session": {"id": sess.id, "title": sess.title, "locale": sess.locale},
        "totals": totals,
        "techniques": dict(techniques),
        "groups": groups_view,
    })


@bp_agile_product_thinking.post("/groups/<int:group_id>/reset")
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
    AgileTrainingProductThinkingAnswer.query.filter_by(group_id=g.id).delete()
    db.session.commit()
    return jsonify({"reset": True})

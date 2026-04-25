"""
Problem discovery dialog API — human interviewer vs simulated user (OpenAI).

POST /api/problem-discovery/reply
POST /api/problem-discovery/synthesize
GET  /api/problem-discovery/health

Mock when OPENAI_API_KEY is missing or PROBLEM_DISCOVERY_MOCK=1.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any, List, Optional

from flask import Blueprint, jsonify, request

from problem_discovery_prompts import (
    REPLY_JSON_INSTRUCTION,
    SYNTH_JSON_INSTRUCTION,
    build_reply_user_prompt,
    build_synthesis_user_prompt,
    system_persona_messenger,
)

logger = logging.getLogger(__name__)

bp_problem_discovery = Blueprint("problem_discovery", __name__, url_prefix="/api/problem-discovery")

MAX_MESSAGES_DEFAULT = 40
MAX_TURNS_DEFAULT = 24
MAX_REPLY_CHARS = 4000


def _normalize_locale(raw: Any) -> str:
    if not raw or not isinstance(raw, str):
        return "en"
    s = raw.strip().lower().split("-", 1)[0]
    return "ru" if s == "ru" else "en"


def _mock_mode() -> bool:
    if os.getenv("PROBLEM_DISCOVERY_MOCK", "").strip().lower() in ("1", "true", "yes"):
        return True
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return True
    return False


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _is_gpt5_model(model: str) -> bool:
    return "gpt-5" in (model or "").strip().lower().split("/")[-1]


def _call_openai(
    system_content: str,
    user_prompt: str,
    *,
    temperature: float = 0.55,
    max_out_tokens: int = 2500,
) -> str:
    from openai import OpenAI

    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=timeout)
    model = (os.getenv("PROBLEM_DISCOVERY_MODEL") or os.getenv("INTERVIEW_SIMULATOR_MODEL") or "gpt-4.1-mini").strip()
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt},
    ]
    kwargs: dict = {"model": model, "messages": messages}
    if _is_gpt5_model(model):
        kwargs["max_completion_tokens"] = max_out_tokens
    else:
        kwargs["temperature"] = max(0.0, min(1.5, temperature))
        kwargs["max_tokens"] = max_out_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _validate_messages(raw: Any) -> Optional[List[dict[str, Any]]]:
    if not isinstance(raw, list):
        return None
    out: List[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant"):
            return None
        if not isinstance(content, str):
            return None
        c = content.strip()
        if len(c) > 16000:
            return None
        out.append({"role": role, "content": c})
    return out


def _mock_reply(locale: str, messages: List[dict[str, Any]]) -> dict:
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = (m.get("content") or "")[:200]
            break
    if locale == "ru":
        reply = (
            "Да, понимаю вопрос. У нас в работе два мессенджера: один корпоративный, второй — с подрядчиками. "
            "Часто теряются вложения при слабом канале, а поиск по истории почти не работает — приходится скроллить. "
            f"Про ваш контекст: «{last_user or '…'}» — могу рассказать подробнее, если уточните ситуацию."
        )
    else:
        reply = (
            "Sure — we juggle two messengers: one internal, one for vendors. "
            "Attachments often fail on bad networks, and search across history is weak so we scroll manually. "
            f"On your last point (\"{last_user or '…'}\"), I can go deeper if you narrow the scenario."
        )
    return {
        "reply": reply[:MAX_REPLY_CHARS],
        "dialogue_complete": False,
        "message_id": str(uuid.uuid4()),
        "mock": True,
    }


def _mock_synthesis(locale: str) -> dict:
    if locale == "ru":
        return {
            "facts": [
                "В организации используются несколько каналов коммуникации.",
                "Есть проблемы с вложениями при нестабильной сети.",
            ],
            "pain_points": ["Слабый поиск по истории переписок", "Фрагментация между мессенджерами"],
            "constraints": ["Требования ИБ к хранению данных", "Привычка контрагентов к привычным приложениям"],
            "open_questions": ["Какие сценарии критичны в первую очередь для вашего домена?"],
            "summary": "Мок-синтез: в реальном режиме список строится из вашего диалога. Подключите OPENAI_API_KEY на сервере.",
            "mock": True,
        }
    return {
        "facts": [
            "The organization uses multiple communication channels.",
            "Attachments struggle on unreliable networks.",
        ],
        "pain_points": ["Weak history search", "Fragmentation across messengers"],
        "constraints": ["Security policies on data residency", "External partners' app habits"],
        "open_questions": ["Which scenarios matter most in your domain first?"],
        "summary": "Mock synthesis: with a live API key, this block is generated from your transcript.",
        "mock": True,
    }


@bp_problem_discovery.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "mock": _mock_mode()}), 200


@bp_problem_discovery.route("/reply", methods=["POST"])
def post_reply():
    try:
        body = request.get_json(force=True, silent=True) or {}
        locale = _normalize_locale(body.get("locale"))
        messages = _validate_messages(body.get("messages"))
        if messages is None:
            return jsonify({"success": False, "error": "messages must be a list of {role, content}"}), 400
        try:
            cap = int(os.getenv("PROBLEM_DISCOVERY_MAX_MESSAGES", str(MAX_MESSAGES_DEFAULT)))
        except ValueError:
            cap = MAX_MESSAGES_DEFAULT
        cap = max(8, min(80, cap))
        if len(messages) > cap:
            messages = messages[-cap:]

        max_turns = int(body.get("maxTurns") or MAX_TURNS_DEFAULT)
        max_turns = max(4, min(60, max_turns))
        user_turns = sum(1 for m in messages if m.get("role") == "user")

        if not messages:
            if _mock_mode():
                opening = (
                    "Здравствуйте, я готов ответить на вопросы про то, как мы пользуемся мессенджерами на работе — "
                    "про удобство, сбои и ограничения. С чего начнём?"
                    if locale == "ru"
                    else "Hi — I'm happy to answer questions about how we use messengers at work: friction, outages, constraints. What would you like to know first?"
                )
                return jsonify(
                    {
                        "success": True,
                        "reply": opening,
                        "dialogue_complete": False,
                        "message_id": str(uuid.uuid4()),
                        "mock": True,
                    }
                ), 200
            open_prompt = (
                "The interview is starting. The interviewer has not asked anything yet. "
                "Give a short natural self-introduction (2–4 sentences) in character as the simulated user "
                "from the system persona — ready for a problem discovery interview about workplace messengers. "
                "Do not ask a long list of questions; one optional short invitation to ask is fine."
                + "\n\n"
                + REPLY_JSON_INSTRUCTION
            )
            system = system_persona_messenger(locale)
            try:
                temp = float(os.getenv("PROBLEM_DISCOVERY_TEMP", "0.55"))
            except ValueError:
                temp = 0.55
            raw = _call_openai(system, open_prompt, temperature=temp, max_out_tokens=800)
            data = _extract_json_object(raw)
            if not data or "reply" not in data:
                logger.warning("Bad opening JSON: %s", raw[:500])
                return jsonify({"success": False, "error": "Invalid AI response"}), 502
            reply = (data.get("reply") or "").strip()
            if len(reply) > MAX_REPLY_CHARS:
                reply = reply[:MAX_REPLY_CHARS] + "…"
            return jsonify(
                {
                    "success": True,
                    "reply": reply,
                    "dialogue_complete": bool(data.get("dialogue_complete")),
                    "message_id": str(uuid.uuid4()),
                }
            ), 200

        if messages[-1].get("role") != "user":
            return jsonify({"success": False, "error": "last message must be from interviewer (role user)"}), 400
        if user_turns >= max_turns:
            closing = (
                "Спасибо, на этом я закончу — времени на интервью достаточно."
                if locale == "ru"
                else "Thanks — I'll stop here; that's enough for this session."
            )
            return jsonify(
                {
                    "success": True,
                    "reply": closing,
                    "dialogue_complete": True,
                    "message_id": str(uuid.uuid4()),
                }
            ), 200

        if _mock_mode():
            out = _mock_reply(locale, messages)
            return jsonify({"success": True, **out}), 200

        system = system_persona_messenger(locale) + "\n" + REPLY_JSON_INSTRUCTION
        user_prompt = build_reply_user_prompt(messages, locale, max_turns, user_turns)
        try:
            temp = float(os.getenv("PROBLEM_DISCOVERY_TEMP", "0.55"))
        except ValueError:
            temp = 0.55
        raw = _call_openai(system, user_prompt, temperature=temp, max_out_tokens=1800)
        data = _extract_json_object(raw)
        if not data or "reply" not in data:
            logger.warning("Bad reply JSON: %s", raw[:500])
            return jsonify({"success": False, "error": "Invalid AI response"}), 502

        reply = (data.get("reply") or "").strip()
        if len(reply) > MAX_REPLY_CHARS:
            reply = reply[:MAX_REPLY_CHARS] + "…"
        return jsonify(
            {
                "success": True,
                "reply": reply,
                "dialogue_complete": bool(data.get("dialogue_complete")),
                "message_id": str(uuid.uuid4()),
            }
        ), 200
    except Exception as e:
        logger.exception("post_reply: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp_problem_discovery.route("/synthesize", methods=["POST"])
def post_synthesize():
    try:
        body = request.get_json(force=True, silent=True) or {}
        locale = _normalize_locale(body.get("locale"))
        messages = _validate_messages(body.get("messages"))
        if messages is None or not messages:
            return jsonify({"success": False, "error": "non-empty messages required"}), 400
        try:
            cap = int(os.getenv("PROBLEM_DISCOVERY_MAX_MESSAGES", str(MAX_MESSAGES_DEFAULT)))
        except ValueError:
            cap = MAX_MESSAGES_DEFAULT
        cap = max(8, min(80, cap))
        if len(messages) > cap:
            messages = messages[-cap:]

        if _mock_mode():
            syn = _mock_synthesis(locale)
            return jsonify({"success": True, "synthesis": syn}), 200

        system = (
            "You output only the JSON structure requested by the user. "
            "Be faithful to the transcript; do not fabricate quotes."
            + "\n"
            + SYNTH_JSON_INSTRUCTION
        )
        user_prompt = build_synthesis_user_prompt(messages, locale)
        raw = _call_openai(system, user_prompt, temperature=0.35, max_out_tokens=2200)
        data = _extract_json_object(raw)
        if not data or "summary" not in data:
            logger.warning("Bad synthesis JSON: %s", raw[:500])
            return jsonify({"success": False, "error": "Invalid AI response"}), 502

        return jsonify({"success": True, "synthesis": {**data, "mock": False}}), 200
    except Exception as e:
        logger.exception("post_synthesize: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500

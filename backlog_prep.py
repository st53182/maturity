from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from openai import OpenAI
from typing import List, Optional
import json
import os

bp_backlog_prep = Blueprint("backlog_prep", __name__, url_prefix="/api/backlog")

BACKLOG_ASSIST_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "backlog_prep_assist",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "suggested_text": {"type": "string"},
                "suggested_context": {"type": "string"},
            },
            "required": ["suggested_text", "suggested_context"],
            "additionalProperties": False,
        },
    },
}


def _get_openai_client() -> Optional[OpenAI]:
    """Create OpenAI client if the key is present in env."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _build_prompt(text: str, work_type: str, context: Optional[str], language: str) -> List[dict]:
    system = (
        "Ты опытный Agile-коуч и бизнес-аналитик. Помогай уточнять user story или epic "
        "по канонам INVEST, дополни акцепт-критерии (если не хватает), "
        "и обязательно возвращай JSON с ключами missing_fields, questions, "
        "suggestions, improved_example. Используй тот же язык ответа, что указал пользователь."
    )
    user = (
        f"Тип: {work_type}\n"
        f"Язык ответа: {language}\n"
        f"Описание:\n{text}\n"
        f"Контекст/цель:\n{context or 'не указано'}\n"
        "Верни только JSON без markdown."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


@bp_backlog_prep.route("/prep", methods=["POST"])
def prepare_backlog_item():
    data = request.get_json() or {}
    description = data.get("text", "").strip()
    work_type = data.get("work_type", "story").strip() or "story"
    context = (data.get("context") or "").strip() or None
    language = (data.get("language") or "ru").strip() or "ru"

    if not description:
        return jsonify({"error": "Описание (text) обязательно"}), 400

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OPENAI_API_KEY не задан"}), 500

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_prompt(description, work_type, context, language),
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = completion.choices[0].message.content
        payload = json.loads(content)
        # Normalize expected keys
        result = {
            "missing_fields": payload.get("missing_fields", []),
            "questions": payload.get("questions") or payload.get("clarifying_questions", []),
            "suggestions": payload.get("suggestions", []),
            "improved_example": payload.get("improved_example", ""),
        }
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "AI_generation_failed", "details": str(exc)}), 500


@bp_backlog_prep.route("/prep/assist", methods=["POST"])
@jwt_required()
def prep_form_assist():
    """Черновик описания и контекста по короткой заметке пользователя (заполнение формы)."""
    data = request.get_json() or {}
    hint = (data.get("hint") or "").strip()
    work_type = (data.get("work_type") or "story").strip() or "story"
    language = (data.get("language") or "ru").strip() or "ru"
    existing_text = (data.get("existing_text") or "").strip()
    existing_context = (data.get("existing_context") or "").strip()

    if not hint and not existing_text:
        return jsonify({"error": "Укажите заметку (hint) или частичное описание"}), 400

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OPENAI_API_KEY не задан"}), 500

    lang_line = "Russian" if language.startswith("ru") else "English"
    system = (
        f"You help product owners draft backlog items. Output language: {lang_line}. "
        "Return only JSON: suggested_text (full draft user story or epic description in INVEST spirit), "
        "suggested_context (team, goal, risks, dependencies — short). "
        "If user provided partial existing_text or existing_context, improve and merge, do not discard useful parts."
    )
    user = (
        f"work_type: {work_type}\n"
        f"user_hint: {hint or '(none)'}\n"
        f"existing_description:\n{existing_text or '(empty)'}\n"
        f"existing_context:\n{existing_context or '(empty)'}\n"
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format=BACKLOG_ASSIST_SCHEMA,
            temperature=0.45,
        )
        payload = json.loads(completion.choices[0].message.content)
        return jsonify(
            {
                "suggested_text": (payload.get("suggested_text") or "").strip(),
                "suggested_context": (payload.get("suggested_context") or "").strip(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "AI_generation_failed", "details": str(exc)}), 500

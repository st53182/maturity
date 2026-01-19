from flask import Blueprint, jsonify, request
from openai import OpenAI
from typing import List, Optional
import json
import os

bp_backlog_prep = Blueprint("backlog_prep", __name__, url_prefix="/api/backlog")


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

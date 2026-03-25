"""ИИ-пояснения по практикам раздела «Agile инструменты»."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from openai import OpenAI

bp_agile_tools_ai = Blueprint("agile_tools_ai", __name__)


def _get_openai_client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _locale_label(locale: str) -> str:
    loc = (locale or "ru").strip().lower()
    if loc.startswith("en"):
        return "English"
    return "Russian"


@bp_agile_tools_ai.route("/api/agile-tools/ask", methods=["POST"])
@jwt_required()
def ask_about_practice() -> Any:
    """
    Тело JSON:
      locale — ru | en
      categoryTitle, name, subtitle (опц.), summary, benefit, detail (опц.)
      user_question (опц.) — уточняющий вопрос пользователя
    Ответ: { "reply": "..." }
    """
    data: Dict[str, Any] = request.get_json() or {}
    locale = (data.get("locale") or "ru").strip()[:12]
    lang = _locale_label(locale)

    category = (data.get("categoryTitle") or "").strip()[:500]
    name = (data.get("name") or "").strip()[:300]
    if not name:
        return jsonify({"error": "name is required"}), 400

    subtitle = (data.get("subtitle") or "").strip()[:500]
    summary = (data.get("summary") or "").strip()[:4000]
    benefit = (data.get("benefit") or "").strip()[:4000]
    detail = (data.get("detail") or "").strip()[:8000]
    user_question = (data.get("user_question") or "").strip()[:4000]

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OpenAI API is not configured"}), 503

    system = (
        "You are an experienced agile coach, facilitator, and product practitioner. "
        f"Write entirely in {lang}. "
        "Format the answer in Markdown: use ## and ### for section headings, **bold** for emphasis, "
        "and bullet or numbered lists where helpful. No JSON or fenced code unless a short example is useful. "
        "Be practical: concrete first steps, who to involve, time boxes, facilitation tips, "
        "common pitfalls, and when this practice is a poor fit. "
        "Connect to Scrum, Kanban, or product discovery only where it helps."
    )

    parts = [
        f"Library category: {category}",
        f"Practice name: {name}",
    ]
    if subtitle:
        parts.append(f"Subtitle / aliases: {subtitle}")
    parts.append(f"Short summary (from the app): {summary}")
    parts.append(f"Stated benefits (from the app): {benefit}")
    if detail:
        parts.append(f"Extended in-app description: {detail}")

    user_msg = "\n".join(parts)
    if user_question:
        user_msg += (
            f"\n\nThe user asks:\n{user_question}\n\n"
            "Answer this question directly, building on the practice context above. "
            "If the question is vague, briefly clarify assumptions."
        )
    else:
        user_msg += (
            "\n\nProvide a deeper practical guide for a Scrum Master, team lead, or product person: "
            "how to introduce the practice, a sample agenda or workshop flow, what \"good\" looks like, "
            "2–3 anti-patterns, and how to measure whether it is helping. "
            "Aim for roughly 400–700 words unless the practice is very narrow."
        )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=2200,
        )
        reply = (resp.choices[0].message.content or "").strip()
        return jsonify({"reply": reply}), 200
    except Exception as e:
        print(f"agile_tools_ai ask: {e}")
        return jsonify({"error": "AI request failed"}), 500

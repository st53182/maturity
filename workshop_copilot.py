"""AI-помощник для тренажёров «продуктовые воркшопы» (без оценки «правильно/неправильно»)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request
from openai import OpenAI

from ai_limits import AiLimitExceeded, check_and_consume_ai_quota

bp_workshop_copilot = Blueprint("workshop_copilot", __name__, url_prefix="/api/agile-training/ws-copilot")


def _client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _lang(locale: str) -> str:
    return "English" if (locale or "").lower().startswith("en") else "Russian"


@bp_workshop_copilot.post("/assist")
def assist() -> Any:
    """body: { exercise_key, step, user_text, locale, context (optional) } -> { reply, fallback? }"""
    try:
        check_and_consume_ai_quota()
    except AiLimitExceeded as e:
        return jsonify({"error": e.message}), 429

    data: Dict = request.get_json(silent=True) or {}
    exercise = (data.get("exercise_key") or "").strip()[:32]
    step = (data.get("step") or "").strip()[:200]
    user_text = (data.get("user_text") or "").strip()[:8000]
    locale = (data.get("locale") or "ru").strip()[:8]
    extra = (data.get("context") or "").strip()[:4000]

    if not exercise or exercise not in {
        "product_stories", "user_story_map", "kanban_system",
    }:
        return jsonify({"error": "exercise_key required"}), 400

    client = _client()
    if not client:
        return jsonify({
            "reply": _fallback_text(locale, exercise, step, user_text),
            "fallback": True,
        }), 200

    lang = _lang(locale)
    system = (
        f"You are a friendly product-thinking coach. Write in {lang} only. "
        "The learner may not be in IT. "
        "NEVER say 'right/wrong' or score the user. No grades. "
        "Ask 1–3 short clarifying questions, then offer ONE improved example draft, "
        "then 2 short bullets: what to refine next. "
        "If input is empty, offer a gentle start template."
    )
    user_msg = f"Workshop: {exercise}\nCurrent step: {step}\nLearner text:\n{user_text or '(empty)'}"
    if extra:
        user_msg += f"\n\nContext:\n{extra}"

    try:
        r = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.45,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        )
        reply = (r.choices[0].message.content or "").strip()
        return jsonify({"reply": reply, "fallback": False}), 200
    except Exception as e:
        print("workshop_copilot", e)
        return jsonify({
            "reply": _fallback_text(locale, exercise, step, user_text),
            "fallback": True,
        }), 200


def _fallback_text(locale: str, exercise: str, step: str, user_text: str) -> str:
    ru = locale != "en"
    if not user_text:
        if ru:
            return "Начните с одной фразы: кто пользователь, что он хочет сделать, зачем. Я подскажу, как сделать формулировку яснее — когда будет текст."
        return "Start with one sentence: who the user is, what they want to do, and why. I can help refine once you have a draft."
    if ru:
        return (
            "AI временно недоступен. Пока вручную проверьте: понятен ли контекст, "
            f"одно ли намерение в тексте, видна ли польза. Шаг: {step}."
        )
    return (
        f"AI is offline. Check manually: is the context clear, is there a single intent, and is the value visible? Step: {step}."
    )

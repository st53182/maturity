"""AI suggestions for the Project management map (project card) sections."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from openai import OpenAI

bp_project_card_ai = Blueprint("project_card_ai", __name__)


def _get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _locale_label(locale: str) -> str:
    loc = (locale or "ru").strip().lower()
    if loc.startswith("en"):
        return "English"
    return "Russian"


ALLOWED_SECTIONS = frozenset(
    {"tasks", "priorities", "dependencies", "bottlenecks", "roles", "decisions"}
)


def _system_prompt(locale: str) -> str:
    lang = _locale_label(locale)
    return (
        "You help fill a one-page «project management map» for delivery teams. "
        f"Respond with a single JSON object only, no markdown or commentary. Write human-readable content in {lang}. "
        "Use realistic but generic examples (no real company names)."
    )


def _user_prompt(section: str, project_name: str, form: Dict[str, Any]) -> str:
    ctx = json.dumps(form, ensure_ascii=False)[:12000]
    pn = project_name or "(unnamed project)"

    if section == "tasks":
        return (
            f"Project: {pn}\nCurrent form JSON (may be partial):\n{ctx}\n\n"
            'Return JSON: {"tasks":[{"name":"","status":"done|progress|risk|waiting","deadline":"","who":""}]} '
            "with 3 to 6 tasks. status must be one of the four values."
        )
    if section == "priorities":
        return (
            f"Project: {pn}\nCurrent form JSON:\n{ctx}\n\n"
            'Return JSON: {"must":["",""],"should":["",""],"nice":["",""]} '
            "each array 1–4 short lines."
        )
    if section == "dependencies":
        return (
            f"Project: {pn}\nCurrent form JSON:\n{ctx}\n\n"
            "Describe cross-team / external dependencies in plain prose (like a Scrum narrative): "
            "who we depend on, what blocks us, what we are waiting for. "
            'Return JSON: {"text":"..."} with 2–5 sentences.'
        )
    if section == "bottlenecks":
        return (
            f"Project: {pn}\nCurrent form JSON:\n{ctx}\n\n"
            'Return JSON: {"items":[{"title":"","desc":""}]} with 2 or 3 bottleneck items.'
        )
    if section == "roles":
        return (
            f"Project: {pn}\nCurrent form JSON:\n{ctx}\n\n"
            'Return JSON: {"roles":[{"name":"","tasksCount":0,"overloadRisk":"normal|medium|high|critical"}]} '
            "with 3–5 roles typical for a product initiative."
        )
    if section == "decisions":
        return (
            f"Project: {pn}\nCurrent form JSON:\n{ctx}\n\n"
            'Return JSON: {"decisions":[{"question":"","context":""}]} with 2 or 3 open decisions.'
        )
    return ""


@bp_project_card_ai.route("/api/project-card/ai-suggest", methods=["POST"])
@jwt_required()
def ai_suggest():
    data: Dict[str, Any] = request.get_json() or {}
    section = (data.get("section") or "").strip().lower()
    if section not in ALLOWED_SECTIONS:
        return jsonify({"error": "invalid section"}), 400

    locale = (data.get("locale") or "ru").strip()[:12]
    project_name = (data.get("projectName") or "").strip()[:500]
    form = data.get("form") if isinstance(data.get("form"), dict) else {}

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OpenAI API is not configured"}), 503

    user_msg = _user_prompt(section, project_name, form)
    if not user_msg:
        return jsonify({"error": "unsupported section"}), 400

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": _system_prompt(locale)},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.45,
            max_tokens=2500,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        return jsonify({"success": True, "section": section, "data": parsed}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "AI returned invalid JSON"}), 502
    except Exception as e:
        print(f"project_card_ai: {e}")
        return jsonify({"error": "AI request failed"}), 500

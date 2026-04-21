"""Strategy Builder API.

Helps company / department / team owners draft their Vision, Mission,
Purpose and Strategy statements, with example snippets and AI assistance
per section.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from openai import OpenAI

bp_strategy_builder = Blueprint(
    "strategy_builder", __name__, url_prefix="/api/strategy-builder"
)

ALLOWED_SECTIONS = frozenset(
    {"vision", "mission", "purpose", "values", "strategy", "okrs", "all"}
)
ALLOWED_SCOPES = frozenset({"company", "department", "team"})


def _openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _locale_label(locale: str) -> str:
    return "English" if (locale or "ru").lower().startswith("en") else "Russian"


def _system_prompt(locale: str, scope: str) -> str:
    lang = _locale_label(locale)
    scope_name = {
        "company": "whole company",
        "department": "department / function",
        "team": "single team",
    }.get(scope, "organization")
    return (
        f"You are a seasoned strategy coach helping a {scope_name} owner articulate "
        "their Vision, Mission, Purpose, core Values and a pragmatic 1–3 year strategy. "
        "Be concise, concrete and actionable — no generic corporate filler. "
        f"Write all content in {lang}. "
        "Respond with a single JSON object only, no markdown, no commentary."
    )


def _full_schema_prompt(form: Dict[str, Any], scope: str, industry: str) -> str:
    ctx = json.dumps(form, ensure_ascii=False)[:6000]
    return (
        f"Scope: {scope}. Industry / context: {industry or 'not specified'}.\n"
        f"Current draft JSON (may be partial):\n{ctx}\n\n"
        'Return JSON of exactly this shape:\n'
        '{\n'
        '  "vision": "one vivid sentence about the future we want to create (3–5 years)",\n'
        '  "mission": "one sentence: for whom we do what, and the change we deliver",\n'
        '  "purpose": "the deeper «why» — what we believe in",\n'
        '  "values": ["3–5 short values, 1–3 words each"],\n'
        '  "strategy": {\n'
        '      "horizon": "e.g. 2026–2028",\n'
        '      "pillars": [ {"name": "strategic pillar", "description": "what & why"} ],\n'
        '      "bets": ["3–5 concrete bets / initiatives for the next 12 months"],\n'
        '      "metrics": ["3–5 outcome metrics — not output"]\n'
        '  },\n'
        '  "okrs": [\n'
        '      {"objective": "qualitative objective", "key_results": ["measurable KR","measurable KR"]}\n'
        '  ]\n'
        '}\n'
        "Aim for specificity. If the draft has content, polish and extend it; "
        "if a field is empty, generate a realistic proposal."
    )


def _section_prompt(section: str, form: Dict[str, Any], scope: str, industry: str) -> str:
    ctx = json.dumps(form, ensure_ascii=False)[:6000]
    prefix = f"Scope: {scope}. Industry: {industry or 'not specified'}.\nCurrent draft:\n{ctx}\n\n"
    if section == "vision":
        return prefix + 'Return {"vision":"one vivid sentence about the future we want to create"}'
    if section == "mission":
        return prefix + 'Return {"mission":"one sentence about for whom we do what and what changes"}'
    if section == "purpose":
        return prefix + 'Return {"purpose":"our «why» — the deeper belief driving the work"}'
    if section == "values":
        return prefix + 'Return {"values":["3–5 short values, 1–3 words each, no generic fluff"]}'
    if section == "strategy":
        return (
            prefix
            + 'Return {"strategy":{"horizon":"","pillars":[{"name":"","description":""}],'
            '"bets":[""],"metrics":[""]}}. '
            "Give 3–4 pillars, 3–5 bets, 3–5 outcome metrics."
        )
    if section == "okrs":
        return (
            prefix
            + 'Return {"okrs":[{"objective":"","key_results":["",""]}]} '
            "with 2–3 objectives, each with 2–3 measurable KRs for the next quarter."
        )
    return ""


@bp_strategy_builder.route("/ai-suggest", methods=["POST"])
@jwt_required()
def ai_suggest():
    data: Dict[str, Any] = request.get_json() or {}
    section = (data.get("section") or "all").strip().lower()
    if section not in ALLOWED_SECTIONS:
        return jsonify({"error": "invalid section"}), 400

    scope = (data.get("scope") or "team").strip().lower()
    if scope not in ALLOWED_SCOPES:
        scope = "team"

    locale = (data.get("locale") or "ru").strip()[:12]
    industry = str(data.get("industry") or "").strip()[:200]
    form = data.get("form") if isinstance(data.get("form"), dict) else {}

    client = _openai_client()
    if not client:
        return jsonify({"error": "OpenAI API is not configured"}), 503

    if section == "all":
        user_msg = _full_schema_prompt(form, scope, industry)
    else:
        user_msg = _section_prompt(section, form, scope, industry)

    if not user_msg:
        return jsonify({"error": "unsupported section"}), 400

    try:
        resp = client.chat.completions.create(
            model=os.getenv("STRATEGY_BUILDER_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": _system_prompt(locale, scope)},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.55,
            max_tokens=2200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        return jsonify({"success": True, "section": section, "scope": scope, "data": parsed}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "AI returned invalid JSON"}), 502
    except Exception as e:
        print(f"strategy_builder: {e}")
        return jsonify({"error": "AI request failed"}), 500

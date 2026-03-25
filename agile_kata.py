"""API для Agile Kata Canvas: сохранение канвасов и AI (helper / mentor / coach)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI

from database import db
from models import AgileKataCanvas

bp_agile_kata = Blueprint("agile_kata", __name__)


def get_openai_client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def default_canvas_state() -> Dict[str, Any]:
    return {
        "challenge": {"goal": "", "businessContext": "", "metric": ""},
        "target": {"outcome": "", "conditions": ""},
        "current": {"measurable": "", "facts": ""},
        "experiments": [],
        "obstacles": [],
        "selectedObstacleIndex": None,
    }


def normalize_canvas_state(raw: Any) -> Dict[str, Any]:
    base = default_canvas_state()
    if not isinstance(raw, dict):
        return base
    ch = raw.get("challenge") if isinstance(raw.get("challenge"), dict) else {}
    base["challenge"] = {
        "goal": str(ch.get("goal") or "")[:8000],
        "businessContext": str(ch.get("businessContext") or "")[:8000],
        "metric": str(ch.get("metric") or "")[:2000],
    }
    tg = raw.get("target") if isinstance(raw.get("target"), dict) else {}
    base["target"] = {
        "outcome": str(tg.get("outcome") or "")[:8000],
        "conditions": str(tg.get("conditions") or "")[:8000],
    }
    cur = raw.get("current") if isinstance(raw.get("current"), dict) else {}
    base["current"] = {
        "measurable": str(cur.get("measurable") or "")[:8000],
        "facts": str(cur.get("facts") or "")[:8000],
    }
    ex = raw.get("experiments")
    if isinstance(ex, list):
        clean: List[Dict[str, str]] = []
        for item in ex[:30]:
            if not isinstance(item, dict):
                continue
            clean.append(
                {
                    "step": str(item.get("step") or "")[:4000],
                    "hypothesis": str(item.get("hypothesis") or "")[:4000],
                    "result": str(item.get("result") or "")[:4000],
                    "learning": str(item.get("learning") or "")[:4000],
                }
            )
        base["experiments"] = clean
    obs = raw.get("obstacles")
    if isinstance(obs, list):
        base["obstacles"] = [str(o)[:500] for o in obs[:40]]
    sel = raw.get("selectedObstacleIndex")
    if sel is None or sel == "":
        base["selectedObstacleIndex"] = None
    else:
        try:
            idx = int(sel)
            if 0 <= idx < len(base["obstacles"]):
                base["selectedObstacleIndex"] = idx
            else:
                base["selectedObstacleIndex"] = None
        except (TypeError, ValueError):
            base["selectedObstacleIndex"] = None
    return base


def _canvas_summary_for_prompt(canvas: Dict[str, Any]) -> str:
    ch = canvas.get("challenge") or {}
    tg = canvas.get("target") or {}
    cur = canvas.get("current") or {}
    ex = canvas.get("experiments") or []
    obs = canvas.get("obstacles") or []
    sel = canvas.get("selectedObstacleIndex")
    lines = [
        "=== CHALLENGE ===",
        f"Long-term goal: {ch.get('goal', '')}",
        f"Business context: {ch.get('businessContext', '')}",
        f"Metric: {ch.get('metric', '')}",
        "=== TARGET CONDITION ===",
        f"Expected outcome (numbers): {tg.get('outcome', '')}",
        f"Conditions to achieve: {tg.get('conditions', '')}",
        "=== CURRENT CONDITION ===",
        f"Measurable now: {cur.get('measurable', '')}",
        f"Facts: {cur.get('facts', '')}",
        "=== EXPERIMENTS ===",
    ]
    for i, e in enumerate(ex, 1):
        lines.append(
            f"{i}. Step: {e.get('step','')}\n   Hypothesis: {e.get('hypothesis','')}\n"
            f"   Result: {e.get('result','')}\n   Learning: {e.get('learning','')}"
        )
    lines.append("=== OBSTACLES ===")
    for i, o in enumerate(obs):
        mark = " (CURRENT)" if sel == i else ""
        lines.append(f"- {o}{mark}")
    return "\n".join(lines)


def _locale_name(locale: str) -> str:
    loc = (locale or "ru").split("-")[0].lower()[:12]
    names = {
        "ru": "Russian",
        "en": "English",
        "uk": "Ukrainian",
        "de": "German",
        "pl": "Polish",
    }
    return names.get(loc, "Russian" if loc == "ru" else "English")


@bp_agile_kata.route("/api/agile-kata", methods=["GET"])
@jwt_required()
def list_canvases():
    uid = get_jwt_identity()
    rows = (
        AgileKataCanvas.query.filter_by(user_id=uid)
        .order_by(AgileKataCanvas.updated_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in rows])


@bp_agile_kata.route("/api/agile-kata", methods=["POST"])
@jwt_required()
def create_canvas():
    uid = get_jwt_identity()
    data = request.get_json() or {}
    title = (data.get("title") or "Agile Kata").strip()[:255]
    state = normalize_canvas_state(data.get("canvas_state"))
    row = AgileKataCanvas(user_id=uid, title=title or "Agile Kata", canvas_state=state)
    db.session.add(row)
    db.session.commit()
    return jsonify(row.to_dict()), 201


@bp_agile_kata.route("/api/agile-kata/<int:cid>", methods=["GET"])
@jwt_required()
def get_canvas(cid: int):
    uid = get_jwt_identity()
    row = AgileKataCanvas.query.filter_by(id=cid, user_id=uid).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(row.to_dict())


@bp_agile_kata.route("/api/agile-kata/<int:cid>", methods=["PUT"])
@jwt_required()
def update_canvas(cid: int):
    uid = get_jwt_identity()
    row = AgileKataCanvas.query.filter_by(id=cid, user_id=uid).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    if "title" in data:
        t = (data.get("title") or "").strip()[:255]
        if t:
            row.title = t
    if "canvas_state" in data:
        row.canvas_state = normalize_canvas_state(data.get("canvas_state"))
    db.session.commit()
    return jsonify(row.to_dict())


@bp_agile_kata.route("/api/agile-kata/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_canvas(cid: int):
    uid = get_jwt_identity()
    row = AgileKataCanvas.query.filter_by(id=cid, user_id=uid).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})


@bp_agile_kata.route("/api/agile-kata/ai", methods=["POST"])
@jwt_required()
def ai_assist():
    """Режимы: helper | mentor | coach. Тело: mode, locale, canvas_state, user_message (опц.)."""
    data = request.get_json() or {}
    mode = (data.get("mode") or "helper").strip().lower()
    if mode not in ("helper", "mentor", "coach"):
        return jsonify({"error": "Invalid mode"}), 400
    locale = (data.get("locale") or "ru").strip()[:12]
    lang = _locale_name(locale)
    canvas = normalize_canvas_state(data.get("canvas_state"))
    user_msg = (data.get("user_message") or "").strip()[:12000]

    client = get_openai_client()
    if not client:
        return jsonify({"error": "OpenAI API is not configured"}), 500

    summary = _canvas_summary_for_prompt(canvas)

    if mode == "helper":
        system = (
            "You are an Agile Kata assistant. Help the team sharpen their canvas: measurable metrics, "
            "clear facts vs opinions, small experiments (1–3 days). "
            "Reject vague goals like 'improve quality' without numbers—suggest concrete metric phrasing. "
            "Output in the user's language. Use short sections with bullets. No JSON."
        )
        user = (
            f"Language: {lang}.\n\nCanvas:\n{summary}\n\n"
        )
        if user_msg:
            user += f"User request / question:\n{user_msg}\n"
        else:
            user += (
                "Review the canvas. Point out fuzzy wording, missing metrics, and suggest 2–4 concrete "
                "rewrites (especially Challenge metric and Target outcome). Keep it actionable.\n"
            )

    elif mode == "mentor":
        system = (
            "You are an Agile Kata mentor (Mentor–Improver cycle). Guide with ONE primary question at a time, "
            "grounded in what is already on the canvas. Typical sequence: target condition → current condition → "
            "obstacle → next experiment step → expected outcome → when to verify. "
            "Do not dump all questions at once unless the canvas is empty—pick the best next question. "
            f"Reply entirely in {lang}. Warm, concise, 1 short paragraph + optional 1–2 follow-up bullets."
        )
        user = f"Canvas state:\n{summary}\n"
        if user_msg:
            user += f"\nUser wrote:\n{user_msg}\n"

    else:  # coach
        system = (
            "You are an experiment coach for Agile Kata. Critique hypotheses (testable?), size (small enough?), "
            "separate facts from assumptions, and check if 'learning' is recorded. "
            "Suggest one smaller next experiment if needed. Highlight gap between current and target metrics if visible. "
            f"Output in {lang}. Structured bullets, no JSON."
        )
        user = f"Canvas:\n{summary}\n"
        if user_msg:
            user += f"\nUser note:\n{user_msg}\n"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.55,
            max_tokens=1400,
        )
        reply = (resp.choices[0].message.content or "").strip()
        return jsonify({"reply": reply}), 200
    except Exception as e:
        print(f"agile_kata ai: {e}")
        return jsonify({"error": "AI request failed"}), 500


@bp_agile_kata.route("/api/agile-kata/example", methods=["GET"])
def example_template():
    """Публичный пример заполнения (без JWT)."""
    ex = default_canvas_state()
    ex["challenge"] = {
        "goal": "Снизить количество дефектов после релиза",
        "businessContext": "Продуктовая команда, релизы каждые 2 недели, растёт недовольство стейкхолдеров",
        "metric": "Количество дефектов, найденных в продакшене в первые 7 дней после релиза",
    }
    ex["current"] = {
        "measurable": "10 дефектов на релиз в среднем за последние 3 релиза",
        "facts": "Только ручное регрессионное тестирование перед релизом; автотестов нет; CI не гоняет тесты на merge",
    }
    ex["target"] = {
        "outcome": "≤ 2 дефекта на релиз в течение 2 релизов подряд",
        "conditions": "Есть автотесты на критические сценарии; CI блокирует merge при падении тестов; smoke на staging обязателен",
    }
    ex["experiments"] = [
        {
            "step": "Добавить автотесты на 3 критических пользовательских сценария",
            "hypothesis": "Дефекты в проде снизятся минимум на 30% уже на следующем релизе",
            "result": "Снижение примерно на 20%",
            "learning": "Покрытия недостаточно; часть багов ушла в непокрытые области",
        }
    ]
    ex["obstacles"] = [
        "Нет выделенного QA-ресурса на автоматизацию",
        "Слабая инфраструктура тестовых стендов",
    ]
    ex["selectedObstacleIndex"] = 0
    return jsonify(ex)

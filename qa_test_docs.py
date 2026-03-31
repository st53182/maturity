import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import QATestCaseSubmission, QATestPlanSubmission

bp_qa_test_docs = Blueprint("qa_test_docs", __name__, url_prefix="/api/qa-test-docs")


def _openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _uid() -> int:
    return int(get_jwt_identity())


def _safe_score(val) -> int:
    try:
        return max(1, min(10, int(val)))
    except Exception:
        return 5


def _json_from_model_output(content: str) -> dict:
    text = (content or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return {}
    return {}


def _serialize_plan(item: QATestPlanSubmission) -> dict:
    return {
        "id": item.id,
        "owner_user_id": item.owner_user_id,
        "team_name": item.team_name or "",
        "payload": item.payload_json or {},
        "quality_score": item.quality_score,
        "quality_feedback": item.quality_feedback or "",
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _serialize_case(item: QATestCaseSubmission) -> dict:
    return {
        "id": item.id,
        "owner_user_id": item.owner_user_id,
        "team_name": item.team_name or "",
        "payload": item.payload_json or {},
        "quality_score": item.quality_score,
        "quality_feedback": item.quality_feedback or "",
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@bp_qa_test_docs.route("/plan/ai-help", methods=["POST"])
@jwt_required()
def plan_ai_help():
    data = request.json or {}
    section = (data.get("section") or "").strip()
    ask = (data.get("prompt") or "").strip()
    form = data.get("form") if isinstance(data.get("form"), dict) else {}

    if not section and not ask:
        return jsonify({"error": "Передайте section или prompt"}), 400

    prompt = f"""Ты опытный QA Lead. Помоги заполнить русский Test Plan для GrowBoard.

Раздел: {section or "общий"}
Запрос пользователя: {ask or "Предложи улучшение раздела"}

Текущие данные формы:
{json.dumps(form, ensure_ascii=False)}

Верни строго JSON:
{{
  "suggested_text": "готовый текст на русском для выбранного раздела",
  "tips": ["короткий совет 1", "короткий совет 2"]
}}"""
    try:
        client = _openai_client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты QA эксперт. Возвращай только JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=700,
        )
        out = _json_from_model_output(resp.choices[0].message.content or "")
        return jsonify({
            "suggested_text": out.get("suggested_text", ""),
            "tips": out.get("tips", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_test_docs.route("/plan/evaluate", methods=["POST"])
@jwt_required()
def plan_evaluate():
    data = request.json or {}
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    if not payload:
        return jsonify({"error": "Пустой payload"}), 400

    prompt = f"""Оцени качество Test Plan для GrowBoard (русский язык) по шкале 1-10.
Проверь полноту, тестируемость, однозначность, реалистичность подхода и критериев pass/fail.

Документ:
{json.dumps(payload, ensure_ascii=False)}

Ответь строго JSON:
{{"score": 1-10, "feedback": "краткий комментарий на русском", "improvements": ["улучшение 1", "улучшение 2"]}}"""
    try:
        client = _openai_client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты QA эксперт. Возвращай только JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        out = _json_from_model_output(resp.choices[0].message.content or "")
        return jsonify({
            "score": _safe_score(out.get("score")),
            "feedback": out.get("feedback", ""),
            "improvements": out.get("improvements", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_test_docs.route("/plan/submit", methods=["POST"])
@jwt_required()
def plan_submit():
    data = request.json or {}
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    if not payload:
        return jsonify({"error": "Пустой payload"}), 400

    item = QATestPlanSubmission(
        owner_user_id=_uid(),
        team_name=(data.get("team_name") or "").strip() or None,
        payload_json=payload,
        quality_score=_safe_score(data.get("quality_score")) if data.get("quality_score") is not None else None,
        quality_feedback=(data.get("quality_feedback") or "").strip() or None,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "id": item.id})


@bp_qa_test_docs.route("/plan/submissions", methods=["GET"])
@jwt_required()
def plan_list():
    items = (
        QATestPlanSubmission.query
        .filter_by(owner_user_id=_uid())
        .order_by(QATestPlanSubmission.updated_at.desc(), QATestPlanSubmission.created_at.desc())
        .limit(200)
        .all()
    )
    return jsonify({"items": [_serialize_plan(x) for x in items]})


@bp_qa_test_docs.route("/plan/submissions/<int:item_id>", methods=["PUT"])
@jwt_required()
def plan_update(item_id: int):
    item = QATestPlanSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403

    data = request.json or {}
    if "team_name" in data:
        item.team_name = (data.get("team_name") or "").strip() or None
    if "payload" in data and isinstance(data.get("payload"), dict):
        item.payload_json = data.get("payload")
    if "quality_score" in data and data.get("quality_score") is not None:
        item.quality_score = _safe_score(data.get("quality_score"))
    if "quality_feedback" in data:
        item.quality_feedback = (data.get("quality_feedback") or "").strip() or None
    item.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


@bp_qa_test_docs.route("/plan/submissions/<int:item_id>", methods=["DELETE"])
@jwt_required()
def plan_delete(item_id: int):
    item = QATestPlanSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


@bp_qa_test_docs.route("/case/ai-help", methods=["POST"])
@jwt_required()
def case_ai_help():
    data = request.json or {}
    ask = (data.get("prompt") or "").strip()
    form = data.get("form") if isinstance(data.get("form"), dict) else {}
    if not ask and not form:
        return jsonify({"error": "Передайте prompt или form"}), 400

    prompt = f"""Ты QA инженер. Помоги составить русский Test Case для GrowBoard.
Используй формат: шаг, ожидаемый результат, фактический, pass/fail, заметки.

Запрос: {ask or "Предложи полный тест-кейс"}
Текущий документ:
{json.dumps(form, ensure_ascii=False)}

Верни строго JSON:
{{
  "test_description": "краткое описание",
  "steps": [
    {{"step_id": "1.0", "step_description": "...", "expected_results": "...", "actual_results": "", "pass_fail": "", "additional_notes": ""}}
  ],
  "tips": ["совет 1", "совет 2"]
}}"""
    try:
        client = _openai_client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты QA эксперт. Возвращай только JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=900,
        )
        out = _json_from_model_output(resp.choices[0].message.content or "")
        return jsonify({
            "test_description": out.get("test_description", ""),
            "steps": out.get("steps", []),
            "tips": out.get("tips", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_test_docs.route("/case/evaluate", methods=["POST"])
@jwt_required()
def case_evaluate():
    data = request.json or {}
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    if not payload:
        return jsonify({"error": "Пустой payload"}), 400

    prompt = f"""Оцени качество Test Case для GrowBoard по шкале 1-10.
Критерии: покрытие, проверяемость expected results, однозначность шагов, корректность pass/fail, практичность.

Документ:
{json.dumps(payload, ensure_ascii=False)}

Ответ только JSON:
{{"score": 1-10, "feedback": "краткий комментарий", "improvements": ["улучшение 1", "улучшение 2"]}}"""
    try:
        client = _openai_client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты QA эксперт. Возвращай только JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        out = _json_from_model_output(resp.choices[0].message.content or "")
        return jsonify({
            "score": _safe_score(out.get("score")),
            "feedback": out.get("feedback", ""),
            "improvements": out.get("improvements", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_test_docs.route("/case/submit", methods=["POST"])
@jwt_required()
def case_submit():
    data = request.json or {}
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    if not payload:
        return jsonify({"error": "Пустой payload"}), 400

    item = QATestCaseSubmission(
        owner_user_id=_uid(),
        team_name=(data.get("team_name") or "").strip() or None,
        payload_json=payload,
        quality_score=_safe_score(data.get("quality_score")) if data.get("quality_score") is not None else None,
        quality_feedback=(data.get("quality_feedback") or "").strip() or None,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "id": item.id})


@bp_qa_test_docs.route("/case/submissions", methods=["GET"])
@jwt_required()
def case_list():
    items = (
        QATestCaseSubmission.query
        .filter_by(owner_user_id=_uid())
        .order_by(QATestCaseSubmission.updated_at.desc(), QATestCaseSubmission.created_at.desc())
        .limit(200)
        .all()
    )
    return jsonify({"items": [_serialize_case(x) for x in items]})


@bp_qa_test_docs.route("/case/submissions/<int:item_id>", methods=["PUT"])
@jwt_required()
def case_update(item_id: int):
    item = QATestCaseSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403

    data = request.json or {}
    if "team_name" in data:
        item.team_name = (data.get("team_name") or "").strip() or None
    if "payload" in data and isinstance(data.get("payload"), dict):
        item.payload_json = data.get("payload")
    if "quality_score" in data and data.get("quality_score") is not None:
        item.quality_score = _safe_score(data.get("quality_score"))
    if "quality_feedback" in data:
        item.quality_feedback = (data.get("quality_feedback") or "").strip() or None
    item.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


@bp_qa_test_docs.route("/case/submissions/<int:item_id>", methods=["DELETE"])
@jwt_required()
def case_delete(item_id: int):
    item = QATestCaseSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})

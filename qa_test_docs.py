import json
import os
import secrets
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
        "has_share": bool(getattr(item, "share_token", None)),
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _case_access_share_or_jwt(data: dict):
    """Доступ к AI/оценке: валидный share_token или JWT."""
    share_token = (data.get("share_token") or "").strip()
    if share_token:
        item = QATestCaseSubmission.query.filter_by(share_token=share_token).first()
        if not item:
            return False, (jsonify({"error": "Нет доступа"}), 403)
        return True, None
    uid = get_jwt_identity()
    if not uid:
        return False, (jsonify({"error": "Требуется авторизация"}), 401)
    return True, None


@bp_qa_test_docs.route("/plan/ai-help", methods=["POST"])
@jwt_required()
def plan_ai_help():
    data = request.json or {}
    section = (data.get("section") or "").strip()
    ask = (data.get("prompt") or "").strip()
    current_value = (data.get("current_value") or "").strip()
    form = data.get("form") if isinstance(data.get("form"), dict) else {}

    if not section and not ask:
        return jsonify({"error": "Передайте section или prompt"}), 400

    prompt = f"""Ты опытный QA Lead и наставник по тест-документации. Помоги заполнить русский Test Plan для GrowBoard.

Раздел: {section or "общий"}
Текущий текст в этом поле:
{current_value or "(пусто)"}
Запрос пользователя: {ask or "Предложи улучшение раздела"}

Текущие данные формы:
{json.dumps(form, ensure_ascii=False)}

Верни строго JSON:
{{
  "field_explanation": "что означает это поле простыми словами (2-4 предложения)",
  "what_to_write": ["что включить в поле, пункт 1", "пункт 2", "пункт 3"],
  "example_text": "короткий пример заполнения этого поля для GrowBoard",
  "suggested_text": "улучшенный вариант на основе текущего текста (если поле пустое — стартовый черновик)",
  "suggestions": ["вариант 1 улучшения текущего текста", "вариант 2 улучшения текущего текста", "вариант 3 улучшения текущего текста"],
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
        suggestions = out.get("suggestions", [])
        if (not isinstance(suggestions, list)) or (not suggestions):
            fallback = out.get("suggested_text", "")
            suggestions = [fallback] if fallback else []
        what_to_write = out.get("what_to_write", [])
        if not isinstance(what_to_write, list):
            what_to_write = []
        return jsonify({
            "field_explanation": out.get("field_explanation", ""),
            "what_to_write": [str(x).strip() for x in what_to_write if str(x).strip()][:5],
            "example_text": out.get("example_text", ""),
            "suggested_text": out.get("suggested_text", ""),
            "suggestions": suggestions,
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
@jwt_required(optional=True)
def case_ai_help():
    data = request.json or {}
    ok, err = _case_access_share_or_jwt(data)
    if not ok:
        return err[0], err[1]
    ask = (data.get("prompt") or "").strip()
    target_field = (data.get("target_field") or "").strip()
    target_label = (data.get("target_label") or "").strip()
    current_value = (data.get("current_value") or "").strip()
    target_mode = (data.get("target_mode") or "").strip().lower()
    form = data.get("form") if isinstance(data.get("form"), dict) else {}
    if not ask and not form:
        return jsonify({"error": "Передайте prompt или form"}), 400

    if target_field:
        if target_mode == "explain_only":
            prompt = f"""Ты QA наставник. Объясни одно поле Test Case простым языком.

Поле: {target_label or target_field}
Технический путь поля: {target_field}
Текущее значение:
{current_value or "(пусто)"}

Запрос: {ask or "Объясни что это поле означает и что в него писать"}
Текущий документ:
{json.dumps(form, ensure_ascii=False)}

Верни строго JSON:
{{
  "field_explanation": "что означает поле (2-4 предложения)",
  "what_to_write": ["что писать, пункт 1", "пункт 2", "пункт 3"],
  "example_text": "короткий пример для этого поля"
}}"""
        else:
            prompt = f"""Ты QA инженер. Сгенерируй варианты УЛУЧШЕНИЯ текста только для одного поля Test Case на русском языке.
Если поле уже заполнено — сохрани исходный смысл и структуру, улучши ясность, проверяемость и качество формулировки.
Не придумывай другой сценарий и не заменяй смысл.
Если поле пустое — предложи стартовый вариант.

Поле: {target_label or target_field}
Технический путь поля: {target_field}
Текущее значение:
{current_value or "(пусто)"}

Запрос: {ask or "Предложи улучшенный текст для поля"}
Текущий документ:
{json.dumps(form, ensure_ascii=False)}

Верни строго JSON:
{{
  "suggestions": ["вариант 1", "вариант 2", "вариант 3"]
}}"""
    else:
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
        if target_field:
            if target_mode == "explain_only":
                what_to_write = out.get("what_to_write", [])
                if not isinstance(what_to_write, list):
                    what_to_write = []
                return jsonify({
                    "target_field": target_field,
                    "field_explanation": out.get("field_explanation", ""),
                    "what_to_write": [str(x).strip() for x in what_to_write if str(x).strip()][:5],
                    "example_text": out.get("example_text", ""),
                })
            suggestions = out.get("suggestions", [])
            if (not isinstance(suggestions, list)) or (not suggestions):
                fallback = out.get("suggested_text", "")
                suggestions = [fallback] if fallback else []
            return jsonify({
                "suggested_text": suggestions[0] if suggestions else "",
                "suggestions": suggestions,
                "target_field": target_field,
            })
        return jsonify({
            "test_description": out.get("test_description", ""),
            "steps": out.get("steps", []),
            "tips": out.get("tips", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_test_docs.route("/case/evaluate", methods=["POST"])
@jwt_required(optional=True)
def case_evaluate():
    data = request.json or {}
    ok, err = _case_access_share_or_jwt(data)
    if not ok:
        return err[0], err[1]
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


@bp_qa_test_docs.route("/case/submissions/<int:item_id>/share", methods=["POST"])
@jwt_required()
def case_create_share(item_id: int):
    item = QATestCaseSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403
    if not item.share_token:
        item.share_token = secrets.token_urlsafe(32)
        item.updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify({
        "share_token": item.share_token,
        "share_path": f"/qa/test-case?share={item.share_token}",
    })


@bp_qa_test_docs.route("/case/submissions/<int:item_id>/share", methods=["DELETE"])
@jwt_required()
def case_revoke_share(item_id: int):
    item = QATestCaseSubmission.query.get(item_id)
    if not item:
        return jsonify({"error": "Запись не найдена"}), 404
    if item.owner_user_id != _uid():
        return jsonify({"error": "Нет доступа"}), 403
    item.share_token = None
    item.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


@bp_qa_test_docs.route("/case/by-share/<token>", methods=["GET"])
def case_get_by_share(token: str):
    token = (token or "").strip()
    if not token:
        return jsonify({"error": "Нет доступа"}), 403
    item = QATestCaseSubmission.query.filter_by(share_token=token).first()
    if not item:
        return jsonify({"error": "Не найдено"}), 404
    return jsonify(_serialize_case(item))


@bp_qa_test_docs.route("/case/by-share/<token>", methods=["PUT"])
def case_put_by_share(token: str):
    token = (token or "").strip()
    item = QATestCaseSubmission.query.filter_by(share_token=token).first()
    if not item:
        return jsonify({"error": "Не найдено"}), 404

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

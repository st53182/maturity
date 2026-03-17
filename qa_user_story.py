# QA задание 5: пользовательская история + критерии приёмки, оценка нейросетью, пул разработки

import json
import os
from flask import Blueprint, request, jsonify
from database import db
from models import QAUserStorySubmission

bp_qa_user_story = Blueprint("qa_user_story", __name__, url_prefix="/api/qa-user-story")

MIN_SCORE = 8
MIN_AC_COUNT = 10


def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _parse_ac(ac):
    """Принимает массив строк или одну строку (по строкам). Возвращает список непустых строк."""
    if isinstance(ac, list):
        return [str(x).strip() for x in ac if str(x).strip()]
    if isinstance(ac, str):
        return [x.strip() for x in ac.split("\n") if x.strip()]
    return []


@bp_qa_user_story.route("/evaluate", methods=["POST"])
def evaluate():
    """Оценка качества пользовательской истории и критериев приёмки (1–10). Без авторизации."""
    data = request.json or {}
    user_story = (data.get("user_story") or "").strip()
    acceptance_criteria = _parse_ac(data.get("acceptance_criteria") or [])

    if not user_story:
        return jsonify({"error": "Введите пользовательскую историю"}), 400

    ac_count = len(acceptance_criteria)
    ac_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(acceptance_criteria)) if acceptance_criteria else "Не указаны."

    client = get_openai_client()
    prompt = f"""Ты эксперт по требованиям и пользовательским историям.

Пользовательская история:
{user_story}

Критерии приёмки (всего {ac_count}):
{ac_text}

Оцени качество по шкале 1–10. Учитывай: наличие роли/ценности/контекста в истории; критерии измеримы и тестируемы; формулировки однозначны; количество критериев достаточное (ожидается не менее 10 для хорошей истории).

Ответь СТРОГО в формате JSON, без другого текста:
{{"score": <число 1-10>, "feedback": "<короткий комментарий на русском 1-3 предложения>"}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты оцениваешь пользовательские истории. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        content = (response.choices[0].message.content or "").strip()
        try:
            out = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            if start >= 0:
                depth = 0
                end = start
                for i, c in enumerate(content[start:], start):
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                    if depth == 0:
                        end = i
                        break
                try:
                    out = json.loads(content[start:end + 1])
                except json.JSONDecodeError:
                    out = {}
            else:
                out = {}
        score = out.get("score")
        if isinstance(score, (int, float)):
            score = max(1, min(10, int(score)))
        else:
            score = 5
        return jsonify({
            "score": score,
            "feedback": out.get("feedback", ""),
            "ac_count": ac_count,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_qa_user_story.route("/submit", methods=["POST"])
def submit():
    """Сохранить в пул разработки. Проверка: score >= 8 и ac_count >= 10. Без авторизации."""
    data = request.json or {}
    team_name = (data.get("team_name") or "").strip()
    user_story = (data.get("user_story") or "").strip()
    acceptance_criteria = data.get("acceptance_criteria")
    score = data.get("score")
    ac_count = data.get("ac_count")

    if not user_story:
        return jsonify({"error": "Введите пользовательскую историю"}), 400

    ac_list = _parse_ac(acceptance_criteria) if acceptance_criteria else []
    ac_count_val = int(ac_count) if ac_count is not None else len(ac_list)
    score_val = int(score) if score is not None else 0

    if score_val < MIN_SCORE or ac_count_val < MIN_AC_COUNT:
        return jsonify({
            "error": f"Для отправки нужна оценка не менее {MIN_SCORE} и не менее {MIN_AC_COUNT} критериев приёмки.",
        }), 400

    ac_json = json.dumps(ac_list, ensure_ascii=False)
    submission = QAUserStorySubmission(
        team_name=team_name,
        user_story=user_story,
        acceptance_criteria=ac_json,
        score=score_val,
        ac_count=ac_count_val,
    )
    db.session.add(submission)
    db.session.commit()
    return jsonify({"success": True, "id": submission.id})


@bp_qa_user_story.route("/submissions", methods=["GET"])
def list_submissions():
    """Список всех отправок (пул разработки). Без авторизации."""
    limit = min(int(request.args.get("limit", 100)), 200)
    submissions = (
        QAUserStorySubmission.query
        .order_by(QAUserStorySubmission.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for s in submissions:
        try:
            ac = json.loads(s.acceptance_criteria) if s.acceptance_criteria else []
        except (TypeError, json.JSONDecodeError):
            ac = []
        out.append({
            "id": s.id,
            "team_name": s.team_name or "",
            "user_story": s.user_story or "",
            "acceptance_criteria": ac,
            "score": s.score,
            "ac_count": s.ac_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return jsonify({"items": out})


@bp_qa_user_story.route("/submissions/<int:sub_id>", methods=["PUT"])
def update_submission(sub_id):
    """Обновить запись в пуле. Без авторизации."""
    submission = QAUserStorySubmission.query.get(sub_id)
    if not submission:
        return jsonify({"error": "Запись не найдена"}), 404

    data = request.json or {}
    if "team_name" in data:
        submission.team_name = str(data["team_name"]).strip()
    if "user_story" in data:
        submission.user_story = str(data["user_story"]).strip()
    if "acceptance_criteria" in data:
        ac = _parse_ac(data["acceptance_criteria"])
        submission.acceptance_criteria = json.dumps(ac, ensure_ascii=False)
        submission.ac_count = len(ac)
    if "score" in data and data["score"] is not None:
        submission.score = max(1, min(10, int(data["score"])))
    db.session.commit()
    return jsonify({"success": True})


@bp_qa_user_story.route("/submissions/<int:sub_id>", methods=["DELETE"])
def delete_submission(sub_id):
    """Удалить запись из пула. Без авторизации."""
    submission = QAUserStorySubmission.query.get(sub_id)
    if not submission:
        return jsonify({"error": "Запись не найдена"}), 404
    db.session.delete(submission)
    db.session.commit()
    return jsonify({"success": True})

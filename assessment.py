from flask import Blueprint, request, jsonify
from openai import OpenAI
from models import Assessment
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

bp_assessment = Blueprint("assessment", __name__)

@bp_assessment.route("/openai_recommend", methods=["POST"])
def openai_recommendations():
    from openai import OpenAI

    data = request.json
    plan = data.get("plan", [])

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if not plan:
        return jsonify({"error": "План не передан"}), 400

    # Формируем текст из плана
    plan_text = "\n".join([f"{idx+1}. {step['text']}" for idx, step in enumerate(plan)])

    prompt = f"""
Ты опытный Agile-коуч. На основе следующего плана по улучшению командной зрелости дай развёрнутые персонализированные рекомендации для каждого элемента плана.

План:
{plan_text}
Используй структурированный HTMl где каждая рекомендация это новый параграф
Рекомендации не должны просто повторять элемент плана, а должны его делать более подробным, детальным, чтобы сразу стало понятно, как это сделать
Формат ответа:
1. Рекомендация — [короткое название]
Рекомендации: [детально, инструменты, роли, ссылки]

2. Рекомендация  — ...
...
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты Agile-коуч, создающий детальные персонализированные рекомендации."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content
        return jsonify({"content": content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_assessment.route("/assessment/<int:assessment_id>/plan", methods=["GET"])
@jwt_required()
def get_improvement_plan(assessment_id):
    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404

    return jsonify({"plan": assessment.plan or []})

@bp_assessment.route("/assessment/<int:assessment_id>/plan", methods=["POST"])
@jwt_required()
def save_improvement_plan(assessment_id):
    data = request.get_json()
    plan = data.get("plan")

    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404

    assessment.plan = plan
    db.session.commit()
    return jsonify({"message": "Plan saved"})

@bp_assessment.route("/generate_plan", methods=["POST"])
def generate_improvement_plan():
    import re
    from openai import OpenAI

    data = request.json
    answer_text = data.get("answer_text")
    assessment_id = data.get("assessment_id")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты опытный Agile-коуч — ИИ Артём. Помоги составить подробный план улучшения командной эффективности."
                },
                {
                    "role": "user",
                    "content": f"""
Вот ответы участников оценки Agile-зрелости:

{answer_text}

На основе этих ответов составь подробный план из 5 шагов по улучшению работы команды. Каждый шаг должен быть:
- Без HTML. Просто текст без форматирования
- С нумерацией: 1. 2. 3. ...
- Конкретным
- Кратко сформулирован (1-2 предложения)
- По SMART
- Реализуемым за 3 месяца
- В виде инструкции
- Если речь идет про обучение — предлагай onagile.ru, но без навязчивости
- Используй SMART
- желательно в формате что, кто и когда
- не использовать слово должен и его вариации
"""
                }
            ],
            temperature=0.6,
            max_tokens=1500
        )

        raw = response.choices[0].message.content

        # 🧠 Разбиваем по нумерации: 1. ..., 2. ..., 3. ...
        steps = re.findall(r'\d+\.\s+(.*?)(?=\n\d+\.|\Z)', raw, re.DOTALL)
        structured_steps = [{"text": step.strip(), "done": False} for step in steps if step.strip()]

        # 💾 Сохраняем план в Assessment
        if assessment_id:
            assessment = Assessment.query.get(assessment_id)
            if assessment:
                assessment.plan = structured_steps
                db.session.commit()

        return jsonify({ "steps": structured_steps })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

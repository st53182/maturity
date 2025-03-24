from flask import Blueprint, request, jsonify
from openai import OpenAI
from models import Assessment  # Убедись, что импорт есть
from database import db        # Импорт SQLAlchemy session

bp_assessment = Blueprint("assessment", __name__)

@bp_assessment.route("/openai_recommend", methods=["POST"])
def openai_recommend():
    data = request.json
    answer_text = data.get("answer_text")
    assessment_id = data.get("assessment_id")  # 🆕

    client = OpenAI(api_key="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")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Ты опытный Agile-коуч - ИИ Артём. Анализируй ответы по Agile зрелости команды."
                },
                {
                    "role": "user",
                    "content": f"Ответы:\n{answer_text}\nПредложи 5 улучшений с конкретными практиками, методами, инструкциями что можно сделать чтобы улучшить оценку. . Важно упомянуть что можно обратится за помощью в agilexpert.ru Давай развернутые ответы страясь израсходовать все токены Представь рекомендации в формате **HTML** с ориентацией текста влево и шрифтами взятыми с agilexpert.ru"
                }
            ],
            temperature=0.7,
            max_tokens=5000
        )

        content = response.choices[0].message.content

        # 🧠 Сохраняем рекомендации в assessment
        if assessment_id:
            assessment = Assessment.query.get(assessment_id)
            if assessment:
                assessment.recommendations = content
                db.session.commit()

        return jsonify({"content": content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


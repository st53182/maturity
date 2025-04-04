from flask import Blueprint, request, jsonify
from database import db
from models import Conflict
import os
from openai import OpenAI

bp_conflict = Blueprint("conflict", __name__)

@bp_conflict.route("/api/conflict/resolve", methods=["POST"])
def resolve_conflict():
    data = request.json
    context = data.get("context")
    participants = data.get("participants")
    attempts = data.get("attempts")
    goal = data.get("goal")

    if not all([context, participants, attempts, goal]):
        return jsonify({"error": "Missing input data"}), 400

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
Ты Agile-коуч, фасилитатор конфликтов. На основе следующих данных определи DISC-профили участников, и предложи стратегию разрешения конфликта по модели PINE , но не оборачивай в markdown ```html:

Контекст конфликта:
{context}

Участники конфликта (эмоции, поведение, реакции):
{participants}

Что уже предпринималось:
{attempts}

Цель: {goal}

Структурируй ответ в HTML:
- Определи DISC профили
- Дай советы мне по взаимодействию со второй стороной конфликта
- Важно чтобы мне как тому кто обратился к тебе как коучу за помощью стало понятно что мне делать, чтобы решить этот конфликт, отстояв свою точку зрения и цели
- Предложи как с помощью конструктивного конфликта донести до второй стороны некоректность действия, предложи вариант даилога с этим человеком
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты профессиональный фасилитатор Agile-команд."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4950
        )

        ai_response = response.choices[0].message.content

        # Сохраняем в БД
        conflict = Conflict(
            context=context,
            participants=participants,
            attempts=attempts,
            goal=goal,
            ai_response=ai_response
        )
        db.session.add(conflict)
        db.session.commit()

        return jsonify({"response": ai_response})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Conflict, Employee
from database import db
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
@bp_conflict.route("/conflicts", methods=["POST"])
@jwt_required()
def create_conflict():
    data = request.json
    user_id = get_jwt_identity()

    try:
        conflict = Conflict(
            context=data["context"],
            participants=data["participants"],
            attempts=data["attempts"],
            goal=data["goal"],
            status=data.get("status", "активен"),
            employee_1_id=data.get("employee_1_id"),
            employee_2_id=data.get("employee_2_id")
        )
        db.session.add(conflict)
        db.session.commit()

        # Генерация анализа через OpenAI
        prompt = f"""Ты фасилитатор конфликтов. На основе описания ситуации и поведения сторон, предложи способы разрешения конфликта и как улучшить взаимодействие.
Контекст: {conflict.context}
Участники: {conflict.participants}
Предпринятые действия: {conflict.attempts}
Цель: {conflict.goal}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты фасилитатор конфликтов и Agile-коуч."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        conflict.ai_analysis = response.choices[0].message.content
        db.session.commit()

        return jsonify({
            "id": conflict.id,
            "analysis": conflict.ai_analysis
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
@bp_conflict.route("/conflicts", methods=["GET"])
@jwt_required()
def get_conflicts():
    conflicts = Conflict.query.order_by(Conflict.created_at.desc()).all()

    result = []
    for c in conflicts:
        result.append({
            "id": c.id,
            "context": c.context,
            "participants": c.participants,
            "attempts": c.attempts,
            "goal": c.goal,
            "status": c.status,
            "employee_1": {"id": c.employee_1.id, "name": c.employee_1.name} if c.employee_1 else None,
            "employee_2": {"id": c.employee_2.id, "name": c.employee_2.name} if c.employee_2 else None,
            "ai_analysis": c.ai_analysis,
            "created_at": c.created_at.isoformat()
        })
    return jsonify(result)

@bp_conflict.route("/conflict/<int:conflict_id>", methods=["DELETE"])
@jwt_required()
def delete_conflict(conflict_id):
    conflict = Conflict.query.get(conflict_id)
    if not conflict:
        return jsonify({"error": "Конфликт не найден"}), 404
    db.session.delete(conflict)
    db.session.commit()
    return jsonify({"message": "Удалено"})
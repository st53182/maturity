from flask import Blueprint, request, jsonify
from openai import OpenAI
from models import Employee
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

bp_motivation = Blueprint("motivation", __name__)

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 🔹 Создание сотрудника и анализ AI
@bp_motivation.route("/motivation", methods=["POST"])
@jwt_required()
def get_motivation():
    user_id = get_jwt_identity()
    data = request.json
    emp_id = data.get("id")

    try:
        # 1. Получаем или создаем сотрудника, принадлежащего текущему пользователю
        if emp_id:
            employee = Employee.query.filter_by(id=emp_id, user_id=user_id).first()
            if not employee:
                return jsonify({"error": "Сотрудник не найден"}), 404
        else:
            employee = Employee(user_id=user_id)

        # 2. Обновляем или задаем поля
        employee.name = data["name"]
        employee.role = data["role"]
        employee.team_id = data.get("team_id") or None
        employee.stress = data["stress"]
        employee.communication = data["communication"]
        employee.behavior = data["behavior"]
        employee.feedback = data["feedback"]
        employee.avatar = data.get("avatar", "default.png")

        db.session.add(employee)
        db.session.commit()

        lang = (data.get("lang") or "ru").lower()
        if lang not in ("en", "ru"):
            lang = "ru"

        system_msg = (
            "You are a coach, psychologist, and DISC analyst. Reply entirely in English using the structure requested."
            if lang == "en"
            else "Ты коуч, психолог и DISC-аналитик. Отвечай полностью на русском в запрошенной структуре."
        )

        # 3. Prompt к OpenAI в зависимости от языка
        if lang == "en":
            prompt = f"""You are an Agile coach and DISC specialist. Analyze the employee description, determine DISC type, and give motivation and interaction recommendations.

Output strictly valid HTML only (no markdown fences). Use exactly these section headings as <h3> tags, each followed by content:

<h3>DISC Type: ...</h3>
<p>One line with the profile name and one of D, I, S, C.</p>

<h3>Motivating factors:</h3>
<ul><li>...</li></ul>

<h3>Demotivators:</h3>
<ul><li>...</li></ul>

<h3>Recommendations for manager:</h3>
<ul><li>...</li></ul>

Employee data:
Name: {employee.name}
Role: {employee.role}
Behavior in stressful situations: {employee.stress}
Interaction with others: {employee.communication}
Work behavior: {employee.behavior}
Reactions to criticism and changes: {employee.feedback}
"""
        else:
            prompt = f"""Ты Agile-коуч и DISC-специалист. Проанализируй описание сотрудника, определи тип по DISC и дай рекомендации по мотивации и взаимодействию.

Ответ — только валидный HTML (без markdown-ограждений). Используй ровно такие заголовки разделов в виде <h3>, после каждого — содержимое:

<h3>Тип DISC: ...</h3>
<p>Одна строка с названием профиля и одной из букв D, I, S, C.</p>

<h3>Мотивирующие факторы:</h3>
<ul><li>...</li></ul>

<h3>Демотиваторы:</h3>
<ul><li>...</li></ul>

<h3>Рекомендации для руководителя:</h3>
<ul><li>...</li></ul>

Данные сотрудника:
Имя: {employee.name}
Роль: {employee.role}
Поведение в стрессовой ситуации: {employee.stress}
Взаимодействие с другими: {employee.communication}
Рабочее поведение: {employee.behavior}
Реакции на критику и изменения: {employee.feedback}
"""

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        result_text = response.choices[0].message.content

        # 4. Сохраняем результат AI
        employee.ai_analysis = result_text
        db.session.commit()

        return jsonify({
            "employee_id": employee.id,
            "analysis": result_text
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500




# 🔹 Получить всех сотрудников
@bp_motivation.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    user_id = get_jwt_identity()
    employees = Employee.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": e.id,
        "name": e.name,
        "role": e.role,
        "team_id": e.team_id,
        "stress": e.stress,
        "communication": e.communication,
        "behavior": e.behavior,
        "feedback": e.feedback,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "team_name": e.team.name if e.team else None,
        "avatar": e.avatar or "default.png",
        "ai_analysis": e.ai_analysis
    } for e in employees])



# 🔹 Создание/обновление сотрудника
@bp_motivation.route("/employees", methods=["POST"])
@jwt_required()
def save_employee():
    user_id = get_jwt_identity()
    data = request.json
    emp_id = data.get("id")

    if emp_id:
        employee = Employee.query.filter_by(id=emp_id, user_id=user_id).first()
        if not employee:
            return jsonify({"error": "Сотрудник не найден"}), 404
    else:
        employee = Employee(user_id=user_id)

    # Обновляем поля
    employee.name = data.get("name")
    employee.role = data.get("role")
    employee.team_id = data.get("team_id") or None
    employee.stress = data.get("stress")
    employee.communication = data.get("communication")
    employee.behavior = data.get("behavior")
    employee.feedback = data.get("feedback")
    employee.avatar = data.get("avatar", "default.png")

    db.session.add(employee)
    db.session.commit()
    return jsonify({"message": "Сотрудник сохранён", "id": employee.id})



# 🔹 Получение одного сотрудника по ID
@bp_motivation.route("/employee/<int:employee_id>", methods=["GET"])
@jwt_required()
def get_employee(employee_id):
    user_id = get_jwt_identity()
    employee = Employee.query.filter_by(id=employee_id, user_id=user_id).first()

    if not employee:
        return jsonify({"error": "Сотрудник не найден"}), 404

    return jsonify({
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "team_id": employee.team_id,
        "stress": employee.stress,
        "communication": employee.communication,
        "behavior": employee.behavior,
        "feedback": employee.feedback,
        "avatar": employee.avatar or "default.png",
        "ai_analysis": employee.ai_analysis,
        "created_at": employee.created_at.isoformat() if employee.created_at else None
    })

@bp_motivation.route("/employee/<int:employee_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(employee_id):
    user_id = get_jwt_identity()
    employee = Employee.query.filter_by(id=employee_id, user_id=user_id).first()

    if not employee:
        return jsonify({"error": "Сотрудник не найден"}), 404

    db.session.delete(employee)
    db.session.commit()
    return jsonify({"message": "Сотрудник удалён"})

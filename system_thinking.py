from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import SystemThinkingIceberg
from database import db
import os
import json
from openai import OpenAI

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

bp_system_thinking = Blueprint("system_thinking", __name__)

@bp_system_thinking.route("/api/system-thinking", methods=["POST"])
@jwt_required()
def create_iceberg():
    """Создание нового айсберга системного мышления"""
    user_id = get_jwt_identity()
    data = request.json
    
    iceberg = SystemThinkingIceberg(
        user_id=user_id,
        event=data.get("event", ""),
        current_level="event"
    )
    
    db.session.add(iceberg)
    db.session.commit()
    
    return jsonify(iceberg.to_dict()), 201

@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>", methods=["GET"])
@jwt_required()
def get_iceberg(iceberg_id):
    """Получение айсберга по ID"""
    user_id = get_jwt_identity()
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404
    
    return jsonify(iceberg.to_dict())

@bp_system_thinking.route("/api/system-thinking", methods=["GET"])
@jwt_required()
def list_icebergs():
    """Список всех айсбергов пользователя"""
    user_id = get_jwt_identity()
    icebergs = SystemThinkingIceberg.query.filter_by(user_id=user_id).order_by(SystemThinkingIceberg.created_at.desc()).all()
    
    return jsonify([iceberg.to_dict() for iceberg in icebergs])

@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>/ask-question", methods=["POST"])
@jwt_required()
def ask_question(iceberg_id):
    """Задать вопрос на текущем уровне айсберга"""
    user_id = get_jwt_identity()
    data = request.json
    user_response = data.get("response", "").strip()
    
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404
    
    client = get_openai_client()
    
    # Определяем текущий уровень и вопрос
    level_questions = {
        "event": {
            "question": "А есть ли какой-то паттерн в этой ситуации?",
            "field": "pattern",
            "next_level": "pattern"
        },
        "pattern": {
            "question": "Какая структура, процесс, система, процедура в компании приводит к проблеме?",
            "field": "system_structure",
            "next_level": "system_structure"
        },
        "system_structure": {
            "question": "А есть ли ментальная модель, которая поддерживает эту конструкцию?",
            "field": "mental_model",
            "next_level": "mental_model"
        },
        "mental_model": {
            "question": "Есть ли опыт, который мог сформировать такую ментальную модель?",
            "field": "experience",
            "next_level": "experience"
        }
    }
    
    current_config = level_questions.get(iceberg.current_level)
    if not current_config:
        return jsonify({"error": "Все уровни уже заполнены"}), 400
    
    # Если пользователь ответил "не знаю" или похожее, предлагаем варианты
    if user_response.lower() in ["не знаю", "не знаю", "не знаю.", "не знаю!", "не знаю?", "нет", "нет идей"]:
        # Генерируем варианты через AI
        context_parts = []
        if iceberg.event:
            context_parts.append(f"Событие: {iceberg.event}")
        if iceberg.pattern:
            context_parts.append(f"Паттерн: {iceberg.pattern}")
        if iceberg.system_structure:
            context_parts.append(f"Системная структура: {iceberg.system_structure}")
        if iceberg.mental_model:
            context_parts.append(f"Ментальная модель: {iceberg.mental_model}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
Ты эксперт по системному мышлению. Пользователь работает над построением айсберга системного мышления.

{context}

Текущий вопрос: {current_config['question']}

Пользователь ответил "не знаю". Предложи 3-5 конкретных вариантов ответа на этот вопрос, которые могут помочь пользователю. 
Ответ должен быть в формате JSON массива строк, например: ["вариант 1", "вариант 2", "вариант 3"]
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по системному мышлению и помогаешь пользователям анализировать проблемы."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            suggestions = ai_response.get("suggestions", [])
            
            if isinstance(suggestions, list):
                return jsonify({
                    "suggestions": suggestions,
                    "question": current_config['question'],
                    "level": iceberg.current_level
                })
            else:
                # Если формат не тот, пытаемся извлечь массив
                suggestions = list(ai_response.values())[0] if ai_response else []
                return jsonify({
                    "suggestions": suggestions if isinstance(suggestions, list) else [],
                    "question": current_config['question'],
                    "level": iceberg.current_level
                })
        except Exception as e:
            return jsonify({"error": f"Ошибка генерации предложений: {str(e)}"}), 500
    
    # Если пользователь дал ответ, сохраняем его
    if user_response:
        setattr(iceberg, current_config['field'], user_response)
        iceberg.current_level = current_config['next_level']
        db.session.commit()
        
        # Если это был последний уровень, генерируем решения
        if iceberg.current_level == "experience":
            iceberg.current_level = "completed"
            db.session.commit()
            
            # Генерируем решения
            return generate_solutions(iceberg)
        
        # Возвращаем следующий вопрос
        next_config = level_questions.get(iceberg.current_level)
        if next_config:
            return jsonify({
                "message": "Ответ сохранен",
                "next_question": next_config['question'],
                "level": iceberg.current_level,
                "iceberg": iceberg.to_dict()
            })
    
    # Если ответа нет, возвращаем текущий вопрос
    return jsonify({
        "question": current_config['question'],
        "level": iceberg.current_level
    })

@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>/save-level", methods=["POST"])
@jwt_required()
def save_level(iceberg_id):
    """Сохранение значения уровня"""
    user_id = get_jwt_identity()
    data = request.json
    
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404
    
    level = data.get("level")
    value = data.get("value", "").strip()
    
    level_fields = {
        "event": "event",
        "pattern": "pattern",
        "system_structure": "system_structure",
        "mental_model": "mental_model",
        "experience": "experience"
    }
    
    if level not in level_fields:
        return jsonify({"error": "Неверный уровень"}), 400
    
    setattr(iceberg, level_fields[level], value)
    
    # Обновляем текущий уровень
    level_order = ["event", "pattern", "system_structure", "mental_model", "experience"]
    try:
        current_index = level_order.index(iceberg.current_level)
        if current_index < len(level_order) - 1:
            iceberg.current_level = level_order[current_index + 1]
    except ValueError:
        pass
    
    db.session.commit()
    
    return jsonify(iceberg.to_dict())

@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>/generate-solutions", methods=["POST"])
@jwt_required()
def generate_solutions_endpoint(iceberg_id):
    """Генерация решений для завершенного айсберга"""
    user_id = get_jwt_identity()
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404
    
    return generate_solutions(iceberg)

def generate_solutions(iceberg):
    """Генерация решений на основе заполненного айсберга"""
    client = get_openai_client()
    
    context = f"""
Событие: {iceberg.event or 'не указано'}
Паттерн поведения: {iceberg.pattern or 'не указано'}
Системная структура: {iceberg.system_structure or 'не указано'}
Ментальная модель: {iceberg.mental_model or 'не указано'}
Опыт: {iceberg.experience or 'не указано'}
"""
    
    prompt = f"""
Ты эксперт по системному мышлению. На основе заполненного айсберга системного мышления предложи 3 решения проблемы:

{context}

Предложи одно решение на уровне системной структуры, одно на уровне ментальной модели и одно на уровне опыта.

Формат ответа - JSON объект с ключами:
- "system_structure_solution": решение на уровне системной структуры (текст)
- "mental_model_solution": решение на уровне ментальной модели (текст)
- "experience_solution": решение на уровне опыта (текст)

Каждое решение должно быть конкретным, практичным и реализуемым.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по системному мышлению и помогаешь находить решения проблем."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )
        
        solutions_data = json.loads(response.choices[0].message.content)
        
        solutions = [
            {
                "level": "system_structure",
                "title": "Решение на уровне системной структуры",
                "text": solutions_data.get("system_structure_solution", "")
            },
            {
                "level": "mental_model",
                "title": "Решение на уровне ментальной модели",
                "text": solutions_data.get("mental_model_solution", "")
            },
            {
                "level": "experience",
                "title": "Решение на уровне опыта",
                "text": solutions_data.get("experience_solution", "")
            }
        ]
        
        iceberg.solutions = solutions
        iceberg.current_level = "completed"
        db.session.commit()
        
        return jsonify({
            "solutions": solutions,
            "iceberg": iceberg.to_dict()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Ошибка генерации решений: {str(e)}"}), 500

@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>", methods=["DELETE"])
@jwt_required()
def delete_iceberg(iceberg_id):
    """Удаление айсберга"""
    user_id = get_jwt_identity()
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404
    
    db.session.delete(iceberg)
    db.session.commit()
    
    return jsonify({"message": "Айсберг удален"}), 200

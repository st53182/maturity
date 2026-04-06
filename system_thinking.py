from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import SystemThinkingIceberg
from database import db
import os
import json
from openai import OpenAI
from ai_limits import check_and_consume_ai_quota

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

bp_system_thinking = Blueprint("system_thinking", __name__)

# Порядок уровней (сверху вниз айсберга). Имя ключа = имя поля в модели.
LEVEL_ORDER = ["event", "pattern", "system_structure", "mental_model", "experience"]

# Вопросы и описания для ИИ по каждому уровню (заполнение в любом порядке).
PER_LEVEL = {
    "event": {
        "question": "Опишите конкретное событие или симптом: что произошло, кто участвовал, когда это заметили?",
        "description": (
            "Событие — видимая часть айсберга: факт, инцидент, симптом. "
            "Пример: «За день до релиза снова отложили поставку из‑за ночных багов»."
        ),
    },
    "pattern": {
        "question": "Какая закономерность или повторяющийся паттерн за этим стоит?",
        "description": (
            "Паттерн — то, что повторяется во времени или при схожих условиях. "
            "Пример: «Третий спринт подряд срываем демо из‑за недотестированных задач»."
        ),
    },
    "system_structure": {
        "question": "Какие структуры, процессы, правила или процедуры в системе поддерживают этот паттерн?",
        "description": (
            "Системная структура — формальные и неформальные процессы, роли, метрики, договорённости. "
            "Пример: «Нет отдельного слота на регресс; приёмка только по чеклисту разработчика»."
        ),
    },
    "mental_model": {
        "question": "Какие убеждения или установки людей поддерживают эту конструкцию?",
        "description": (
            "Ментальная модель — то, во что люди искренне верят и что оправдывает текущее поведение. "
            "Пример: «Тестирование всегда тормозит, лучше быстро выкатить и починить в бою»."
        ),
    },
    "experience": {
        "question": "Какой прошлый опыт мог сформировать такие установки?",
        "description": (
            "Опыт — конкретные ситуации из прошлого, которые укрепили убеждения. "
            "Пример: «Год назад жёсткий дедлайн сорвали из‑за долгих тестов — с тех пор их недооценивают»."
        ),
    },
}


def _iceberg_fully_filled(iceberg) -> bool:
    return all(
        (getattr(iceberg, k) or "").strip()
        for k in LEVEL_ORDER
    )


def _clear_solutions_if_needed(iceberg, fields_updated: bool, resume_level: str = None) -> None:
    if not fields_updated:
        return
    if iceberg.solutions:
        iceberg.solutions = None
    if iceberg.current_level == "completed":
        iceberg.current_level = resume_level if resume_level in LEVEL_ORDER else "experience"

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

@bp_system_thinking.route("/api/system-thinking/level-guide", methods=["GET"])
def level_guide():
    """Справка по уровням айсберга (можно вызывать без JWT для статического контента)."""
    out = []
    titles = {
        "event": "Событие",
        "pattern": "Паттерн поведения",
        "system_structure": "Системная структура",
        "mental_model": "Ментальная модель",
        "experience": "Опыт",
    }
    for i, key in enumerate(LEVEL_ORDER, start=1):
        cfg = PER_LEVEL[key]
        out.append({
            "id": key,
            "order": i,
            "title": titles[key],
            "question": cfg["question"],
            "description": cfg["description"],
        })
    return jsonify({"levels": out})


@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>/save-state", methods=["POST"])
@jwt_required()
def save_state(iceberg_id):
    """Автосохранение полей и активного уровня (произвольный порядок заполнения)."""
    user_id = get_jwt_identity()
    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404

    data = request.json or {}
    fields = data.get("fields")
    active_level = data.get("active_level")

    updated = False
    if isinstance(fields, dict):
        for key in LEVEL_ORDER:
            if key not in fields:
                continue
            val = fields[key]
            if val is None:
                continue
            s = val if isinstance(val, str) else str(val)
            if getattr(iceberg, key) != s:
                updated = True
            setattr(iceberg, key, s)

    _clear_solutions_if_needed(iceberg, updated, active_level if active_level in LEVEL_ORDER else None)

    if active_level in LEVEL_ORDER:
        iceberg.current_level = active_level
    db.session.commit()
    return jsonify(iceberg.to_dict())


@bp_system_thinking.route("/api/system-thinking/<int:iceberg_id>/ask-question", methods=["POST"])
@jwt_required()
def ask_question(iceberg_id):
    """Вопрос по выбранному уровню; ответ сохраняет поле этого уровня без линейного перехода."""
    user_id = get_jwt_identity()
    data = request.json or {}
    user_response = (data.get("response") or "").strip()
    requested_level = data.get("level")

    iceberg = SystemThinkingIceberg.query.filter_by(id=iceberg_id, user_id=user_id).first()
    if not iceberg:
        return jsonify({"error": "Айсберг не найден"}), 404

    if requested_level not in PER_LEVEL:
        requested_level = iceberg.current_level if iceberg.current_level in PER_LEVEL else "event"

    cfg = PER_LEVEL[requested_level]
    client = get_openai_client()

    user_response_lower = user_response.lower().strip()
    dont_know_phrases = [
        "не знаю", "незнаю", "не знаю.", "не знаю!", "не знаю?", "не знаю,",
        "нет", "нет идей", "не понимаю", "не могу ответить", "не знаю что ответить",
        "не знаю что сказать", "затрудняюсь ответить", "не могу придумать",
    ]
    is_dont_know = (
        user_response_lower in dont_know_phrases
        or "не знаю" in user_response_lower
        or user_response_lower.startswith("не знаю")
        or (
            len(user_response_lower) <= 15
            and any(phrase in user_response_lower for phrase in ["не знаю", "незнаю", "не понимаю"])
        )
    )

    if is_dont_know and user_response:
        check_and_consume_ai_quota()
        context_parts = []
        if iceberg.event:
            context_parts.append(f"Событие: {iceberg.event}")
        if iceberg.pattern:
            context_parts.append(f"Паттерн: {iceberg.pattern}")
        if iceberg.system_structure:
            context_parts.append(f"Системная структура: {iceberg.system_structure}")
        if iceberg.mental_model:
            context_parts.append(f"Ментальная модель: {iceberg.mental_model}")
        if iceberg.experience:
            context_parts.append(f"Опыт: {iceberg.experience}")

        context = "\n".join(context_parts) if context_parts else "Пользователь только начал работу над айсбергом."
        level_description = cfg.get("description", "")

        prompt = f"""
Ты эксперт по системному мышлению. Пользователь работает над построением айсберга системного мышления.

{context}

Уровень: {requested_level}
Текущий вопрос: {cfg['question']}
Контекст уровня: {level_description}

Пользователь ответил "не знаю". Предложи 3-5 конкретных вариантов ответа на этот вопрос.
Ответ — JSON с ключом "suggestions" и массивом строк.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "Ты эксперт по системному мышлению и помогаешь пользователям анализировать проблемы."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500,
            )

            ai_response = json.loads(response.choices[0].message.content)
            suggestions = ai_response.get("suggestions", [])
            if not isinstance(suggestions, list):
                for value in ai_response.values():
                    if isinstance(value, list):
                        suggestions = value
                        break

            return jsonify({
                "suggestions": suggestions if isinstance(suggestions, list) and len(suggestions) > 0 else [],
                "question": cfg["question"],
                "level": requested_level,
                "message": "Вот несколько вариантов, которые могут помочь:",
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Ошибка генерации предложений: {str(e)}"}), 500

    if user_response:
        setattr(iceberg, requested_level, user_response)
        if iceberg.current_level != "completed":
            iceberg.current_level = requested_level
        _clear_solutions_if_needed(iceberg, True, requested_level)
        if iceberg.current_level != "completed":
            iceberg.current_level = requested_level
        db.session.commit()
        return jsonify({
            "message": "Ответ сохранен",
            "level": requested_level,
            "iceberg": iceberg.to_dict(),
        })

    return jsonify({
        "question": cfg["question"],
        "level": requested_level,
        "description": cfg.get("description", ""),
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
    
    old_val = getattr(iceberg, level_fields[level])
    setattr(iceberg, level_fields[level], value)
    if (old_val or "") != (value or ""):
        _clear_solutions_if_needed(iceberg, True, level if level in LEVEL_ORDER else None)

    active = data.get("active_level")
    if active in LEVEL_ORDER and iceberg.current_level != "completed":
        iceberg.current_level = active
    elif level in LEVEL_ORDER and iceberg.current_level != "completed":
        iceberg.current_level = level

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

    if not _iceberg_fully_filled(iceberg):
        return jsonify({"error": "Заполните все пять уровней айсберга перед генерацией решений"}), 400
    
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
            model="gpt-4.1",
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

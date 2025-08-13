from flask import Blueprint, request, jsonify
from openai import OpenAI
from models import MeetingDesign, Team
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from datetime import datetime, timedelta

bp_meeting_design = Blueprint("meeting_design", __name__)

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def generate_meeting_prompt(meeting_type, goal, duration, constraints, lang='ru'):
    if lang == 'ru':
        return f"""
Ты опытный фасилитатор встреч. Создай детальный дизайн встречи в формате фасилитационного гайда.

Параметры встречи:
- Тип: {meeting_type}
- Цель: {goal}
- Продолжительность: {duration} минут
- Ограничения: {constraints}

Используй лучшие практики из sessionlab.com и retromat.org для ретроспектив. Включи разнообразные активности: ледоколы, групповые обсуждения, мозговые штурмы, рефлексии.

Формат ответа - JSON массив блоков (БЕЗ дополнительного текста, только JSON):
[
  {{
    "time": "14:00",
    "duration": 10,
    "title": "Введение",
    "description": "Подробное описание активности, включая инструкции для фасилитатора",
    "type": "opening"
  }},
  {{
    "time": "14:10", 
    "duration": 15,
    "title": "Ледокол",
    "description": "Активность для знакомства и разогрева группы",
    "type": "icebreaker"
  }}
]

Типы блоков: opening, icebreaker, discussion, brainstorm, reflection, break, closing
Время должно быть последовательным, общая продолжительность должна соответствовать {duration} минутам.
"""
    else:
        return f"""
You are an experienced meeting facilitator. Create a detailed meeting design in facilitation guide format.

Meeting parameters:
- Type: {meeting_type}
- Goal: {goal}
- Duration: {duration} minutes
- Constraints: {constraints}

Use best practices from sessionlab.com and retromat.org for retrospectives. Include diverse activities: icebreakers, group discussions, brainstorming, reflections.

Response format - JSON array of blocks (NO additional text, only JSON):
[
  {{
    "time": "14:00",
    "duration": 10,
    "title": "Introduction",
    "description": "Detailed activity description including facilitator instructions",
    "type": "opening"
  }}
]

Block types: opening, icebreaker, discussion, brainstorm, reflection, break, closing
Time should be sequential, total duration should match {duration} minutes.
"""

def regenerate_block_prompt(block, meeting_context, lang='ru'):
    if lang == 'ru':
        return f"""
Перегенерируй этот блок встречи с учетом контекста:

Текущий блок:
- Время: {block.get('time')}
- Продолжительность: {block.get('duration')} минут
- Название: {block.get('title')}
- Описание: {block.get('description')}
- Тип: {block.get('type')}

Контекст встречи: {meeting_context}

Создай альтернативную активность того же типа и продолжительности. Используй практики из sessionlab.com и retromat.org.

Формат ответа - JSON объект (БЕЗ дополнительного текста):
{{
  "time": "{block.get('time')}",
  "duration": {block.get('duration')},
  "title": "Новое название",
  "description": "Новое подробное описание активности",
  "type": "{block.get('type')}"
}}
"""
    else:
        return f"""
Regenerate this meeting block considering the context:

Current block:
- Time: {block.get('time')}
- Duration: {block.get('duration')} minutes
- Title: {block.get('title')}
- Description: {block.get('description')}
- Type: {block.get('type')}

Meeting context: {meeting_context}

Create an alternative activity of the same type and duration. Use practices from sessionlab.com and retromat.org.

Response format - JSON object (NO additional text):
{{
  "time": "{block.get('time')}",
  "duration": {block.get('duration')},
  "title": "New title",
  "description": "New detailed activity description",
  "type": "{block.get('type')}"
}}
"""

@bp_meeting_design.route("/api/meeting-design/generate", methods=["POST"])
@jwt_required()
def generate_meeting_design():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        meeting_type = data.get('meeting_type')
        goal = data.get('goal')
        duration = data.get('duration_minutes')
        constraints = data.get('constraints', '')
        team_id = data.get('team_id')
        title = data.get('title', f"{meeting_type} - {goal[:50]}")
        
        if not all([meeting_type, goal, duration]):
            return jsonify({"error": "Отсутствуют обязательные поля"}), 400
        
        prompt = generate_meeting_prompt(meeting_type, goal, duration, constraints)
        
        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500
        
        response = client.chat.completions.create(
            model="chatgpt-5",
            messages=[
                {"role": "system", "content": "Ты эксперт по фасилитации встреч. Отвечай только в формате JSON без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
        )
        
        blocks_text = response.choices[0].message.content.strip()
        
        try:
            blocks = json.loads(blocks_text)
        except json.JSONDecodeError:
            blocks_text = blocks_text.replace('```json', '').replace('```', '').strip()
            blocks = json.loads(blocks_text)
        
        meeting_design = MeetingDesign(
            user_id=user_id,
            team_id=team_id,
            title=title,
            meeting_type=meeting_type,
            goal=goal,
            duration_minutes=duration,
            constraints=constraints,
            blocks=blocks
        )
        
        db.session.add(meeting_design)
        db.session.commit()
        
        return jsonify(meeting_design.to_dict()), 201
        
    except Exception as e:
        print(f"Error generating meeting design: {str(e)}")
        return jsonify({"error": "Ошибка генерации дизайна встречи"}), 500

@bp_meeting_design.route("/api/meeting-design/regenerate-block", methods=["POST"])
@jwt_required()
def regenerate_block():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        design_id = data.get('design_id')
        block_index = data.get('block_index')
        
        meeting_design = MeetingDesign.query.filter_by(id=design_id, user_id=user_id).first()
        if not meeting_design:
            return jsonify({"error": "Дизайн встречи не найден"}), 404
        
        if block_index >= len(meeting_design.blocks):
            return jsonify({"error": "Блок не найден"}), 404
        
        current_block = meeting_design.blocks[block_index]
        meeting_context = f"Тип: {meeting_design.meeting_type}, Цель: {meeting_design.goal}"
        
        prompt = regenerate_block_prompt(current_block, meeting_context)
        
        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты эксперт по фасилитации встреч. Отвечай только в формате JSON без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        new_block_text = response.choices[0].message.content.strip()
        
        try:
            new_block = json.loads(new_block_text)
        except json.JSONDecodeError:
            new_block_text = new_block_text.replace('```json', '').replace('```', '').strip()
            new_block = json.loads(new_block_text)
        
        meeting_design.blocks[block_index] = new_block
        meeting_design.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({"block": new_block, "design": meeting_design.to_dict()}), 200
        
    except Exception as e:
        print(f"Error regenerating block: {str(e)}")
        return jsonify({"error": "Ошибка перегенерации блока"}), 500

@bp_meeting_design.route("/api/meeting-design", methods=["GET"])
@jwt_required()
def get_meeting_designs():
    try:
        user_id = get_jwt_identity()
        designs = MeetingDesign.query.filter_by(user_id=user_id).order_by(MeetingDesign.created_at.desc()).all()
        return jsonify([design.to_dict() for design in designs]), 200
    except Exception as e:
        print(f"Error fetching meeting designs: {str(e)}")
        return jsonify({"error": "Ошибка загрузки дизайнов встреч"}), 500

@bp_meeting_design.route("/api/meeting-design/<int:design_id>", methods=["GET"])
@jwt_required()
def get_meeting_design(design_id):
    try:
        user_id = get_jwt_identity()
        design = MeetingDesign.query.filter_by(id=design_id, user_id=user_id).first()
        if not design:
            return jsonify({"error": "Дизайн встречи не найден"}), 404
        return jsonify(design.to_dict()), 200
    except Exception as e:
        print(f"Error fetching meeting design: {str(e)}")
        return jsonify({"error": "Ошибка загрузки дизайна встречи"}), 500

@bp_meeting_design.route("/api/meeting-design/<int:design_id>", methods=["PUT"])
@jwt_required()
def update_meeting_design(design_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        design = MeetingDesign.query.filter_by(id=design_id, user_id=user_id).first()
        if not design:
            return jsonify({"error": "Дизайн встречи не найден"}), 404
        
        if 'title' in data:
            design.title = data['title']
        if 'blocks' in data:
            design.blocks = data['blocks']
        if 'goal' in data:
            design.goal = data['goal']
        if 'constraints' in data:
            design.constraints = data['constraints']
        
        design.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(design.to_dict()), 200
    except Exception as e:
        print(f"Error updating meeting design: {str(e)}")
        return jsonify({"error": "Ошибка обновления дизайна встречи"}), 500

@bp_meeting_design.route("/api/meeting-design/<int:design_id>", methods=["DELETE"])
@jwt_required()
def delete_meeting_design(design_id):
    try:
        user_id = get_jwt_identity()
        design = MeetingDesign.query.filter_by(id=design_id, user_id=user_id).first()
        if not design:
            return jsonify({"error": "Дизайн встречи не найден"}), 404
        
        db.session.delete(design)
        db.session.commit()
        
        return jsonify({"message": "Дизайн встречи удален"}), 200
    except Exception as e:
        print(f"Error deleting meeting design: {str(e)}")
        return jsonify({"error": "Ошибка удаления дизайна встречи"}), 500


@bp_meeting_design.route("/api/teams", methods=["GET"])
@jwt_required()
def get_user_teams():
    try:
        user_id = get_jwt_identity()
        teams = Team.query.filter_by(user_id=user_id).all()
        return jsonify([{"id": team.id, "name": team.name} for team in teams]), 200
    except Exception as e:
        print(f"Error fetching teams: {str(e)}")
        return jsonify({"error": "Ошибка загрузки команд"}), 500

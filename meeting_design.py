from flask import Blueprint, request, jsonify
from openai import OpenAI
from models import MeetingDesign, Team
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from datetime import datetime, timedelta

bp_meeting_design = Blueprint("meeting_design", __name__)

LOCALE_NAMES = {
    "ru": "Russian",
    "en": "English",
    "de": "German",
    "uk": "Ukrainian",
    "es": "Spanish",
    "fr": "French",
    "pl": "Polish",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "kk": "Kazakh",
    "be": "Belarusian",
}


def locale_language_name(locale: str) -> str:
    if not locale:
        return "English"
    base = str(locale).split("-")[0].split("_")[0].lower()
    return LOCALE_NAMES.get(base, "English")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

MEETING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "meeting_design",
        "strict": True,  # запрещает лишние поля и вольный текст
        "schema": {
            "type": "object",
            "properties": {
                "blocks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["time", "duration", "title", "description", "type"],
                        "properties": {
                            "time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
                            "duration": {"type": "integer", "minimum": 1},
                            "title": {"type": "string", "minLength": 1},
                            # просим маркированные пункты — не валидируется схемой, но задаёт стиль
                            "description": {"type": "string", "minLength": 1},
                            "type": {"type": "string", "enum": [
                                "opening","icebreaker","discussion","brainstorm","reflection","break","closing"
                            ]}
                        },
                        "additionalProperties": False
                    }
                }
            },
            "required": ["blocks"],
            "additionalProperties": False
        }
    }
}

TOPIC_SUGGESTIONS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "meeting_conversation_topics",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 3, "maxLength": 200},
                    "minItems": 4,
                    "maxItems": 10,
                }
            },
            "required": ["topics"],
            "additionalProperties": False,
        },
    },
}

ALLOWED_FORM_CONSTRAINT_KEYS = frozenset(
    {
        "remote",
        "inPerson",
        "hybrid",
        "largeGroup",
        "smallGroup",
        "timeboxed",
        "interactive",
        "presentation",
    }
)


def generate_meeting_prompt(meeting_type, goal, duration, constraints, locale="ru"):
    lang_name = locale_language_name(locale)
    return f"""
You are an experienced meeting facilitator. Create a detailed meeting design as a facilitation guide.

IMPORTANT: All human-readable text inside JSON fields (title, description of each block) must be written in {lang_name} (locale: {locale}).

Meeting parameters:
- Type: {meeting_type}
- Goal: {goal}
- Duration: {duration} minutes
- Constraints: {constraints}

Use best practices from sessionlab.com and retromat.org. Include diverse activities: icebreakers, group discussions, brainstorming, reflections.

Return ONLY a JSON object (no text outside JSON) with this structure:
{{
  "blocks": [
    {{
      "time": "14:00",
      "duration": 10,
      "title": "Introduction",
      "description": "- Welcome (30s)\\n- Logistics (60s)\\n- Ground rules (90s)",
      "type": "opening"
    }}
  ]
}}

Requirements:
- "blocks": array of objects with time (HH:MM), duration (integer minutes), title (string), description (string with bullet lines starting with "- "), type (one of: opening, icebreaker, discussion, brainstorm, reflection, break, closing).
- Times sequential, non-overlapping; sum of durations MUST equal {duration}.
- Separate description lines with \\n.
- No extra fields or markdown fences. Valid JSON only.
"""


def regenerate_block_prompt(block, meeting_context, locale="ru"):
    lang_name = locale_language_name(locale)
    return f"""
Regenerate this meeting block. All text in title and description must be in {lang_name}.

Current block:
- Time: {block.get('time')}
- Duration: {block.get('duration')} minutes
- Title: {block.get('title')}
- Description: {block.get('description')}
- Type: {block.get('type')}

Meeting context: {meeting_context}

Create an alternative activity of the same type and duration. Use sessionlab.com and retromat.org style practices.

Return ONLY a JSON object:
{{
  "time": "{block.get('time')}",
  "duration": {block.get('duration')},
  "title": "New title",
  "description": "New detailed activity description with bullet lines",
  "type": "{block.get('type')}"
}}
"""


@bp_meeting_design.route("/api/meeting-design/ai-conversation-topics", methods=["POST"])
@jwt_required()
def ai_conversation_topics():
    """Короткие темы и углы для разговора на заданную тему встречи (язык — locale)."""
    try:
        data = request.get_json() or {}
        theme = (data.get("theme") or "").strip()
        if not theme:
            return jsonify({"error": "Укажите тему или фокус встречи"}), 400
        meeting_type = (data.get("meeting_type") or "general").strip()
        locale = (data.get("locale") or "ru").strip()[:12]
        lang_name = locale_language_name(locale)

        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500

        prompt = f"""
You help facilitators prepare discussion. Meeting type (hint): {meeting_type}.
Focus / theme: {theme}

Generate 4 to 10 SHORT lines. Each line is ONE concise conversation theme or angle (max ~180 characters).
Language: {lang_name}. No numbering in strings. Practical and specific.
Return JSON only with key "topics" (array of strings).
"""
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You output only valid JSON matching the schema. Be concise.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=TOPIC_SUGGESTIONS_SCHEMA,
        )
        out = json.loads(response.choices[0].message.content)
        topics = out.get("topics") or []
        return jsonify({"topics": topics}), 200
    except Exception as e:
        print(f"ai_conversation_topics: {e}")
        return jsonify({"error": "Не удалось получить темы"}), 500


@bp_meeting_design.route("/api/meeting-design/form-assist", methods=["POST"])
@jwt_required()
def form_assist():
    """Черновик названия, цели, ограничений по короткой заметке (до генерации повестки)."""
    try:
        data = request.get_json() or {}
        brief = (data.get("brief_note") or "").strip()
        if not brief:
            return jsonify({"error": "Кратко опишите встречу (brief_note)"}), 400
        meeting_type = (data.get("meeting_type") or "retrospective").strip()
        try:
            duration = int(data.get("duration_minutes") or 60)
        except (TypeError, ValueError):
            duration = 60
        locale = (data.get("locale") or "ru").strip()[:12]
        lang_name = locale_language_name(locale)
        existing_title = (data.get("existing_title") or "").strip()
        existing_goal = (data.get("existing_goal") or "").strip()

        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500

        allowed_list = ", ".join(sorted(ALLOWED_FORM_CONSTRAINT_KEYS))
        prompt = f"""
You help facilitators fill a meeting planning form. All human-readable strings must be in {lang_name}.

Meeting type: {meeting_type}
Duration (minutes): {duration}

User brief (what they want):
{brief}

Current draft (improve/merge; keep useful specifics):
- title: {existing_title or "(empty)"}
- goal: {existing_goal or "(empty)"}

Return ONLY valid JSON with exactly these keys:
"title" (string), "goal" (string), "constraints_notes" (string, extra constraints as text),
"constraint_keys" (array of strings).

constraint_keys must contain ONLY values from this set (subset allowed, can be empty): {allowed_list}
"""
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You output only valid JSON. No markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        out = json.loads(response.choices[0].message.content)
        raw_keys = out.get("constraint_keys") or []
        if not isinstance(raw_keys, list):
            raw_keys = []
        keys = [k for k in raw_keys if isinstance(k, str) and k in ALLOWED_FORM_CONSTRAINT_KEYS]
        return jsonify(
            {
                "title": (out.get("title") or "").strip(),
                "goal": (out.get("goal") or "").strip(),
                "constraints_notes": (out.get("constraints_notes") or "").strip(),
                "constraint_keys": keys,
            }
        ), 200
    except Exception as e:
        print(f"form_assist: {e}")
        return jsonify({"error": "Не удалось заполнить черновик"}), 500


@bp_meeting_design.route("/api/meeting-design/ai-facilitator-help", methods=["POST"])
@jwt_required()
def ai_facilitator_help():
    """Текстовая подсказка фасилитатору (без озвучивания)."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        design_id = data.get("design_id")
        block_index = data.get("block_index")
        question = (data.get("question") or "").strip()
        locale = (data.get("locale") or "ru").strip()[:12]
        lang_name = locale_language_name(locale)

        if not design_id:
            return jsonify({"error": "Не указан design_id"}), 400

        design = MeetingDesign.query.filter_by(id=design_id, user_id=user_id).first()
        if not design:
            return jsonify({"error": "Дизайн встречи не найден"}), 404

        ctx_lines = [
            f"Title: {design.title}",
            f"Type: {design.meeting_type}",
            f"Goal: {design.goal}",
            f"Duration minutes: {design.duration_minutes}",
        ]
        if design.constraints:
            ctx_lines.append(f"Constraints: {design.constraints}")

        if block_index is not None:
            try:
                bi = int(block_index)
            except (TypeError, ValueError):
                return jsonify({"error": "Некорректный block_index"}), 400
            if bi < 0 or bi >= len(design.blocks or []):
                return jsonify({"error": "Блок не найден"}), 404
            b = design.blocks[bi]
            ctx_lines.append(f"Selected block #{bi + 1}: {b.get('time')} {b.get('title')} ({b.get('duration')} min, type {b.get('type')})")
            ctx_lines.append(f"Block description:\n{b.get('description', '')}")
        else:
            ctx_lines.append("Context: whole meeting agenda.")
            for i, b in enumerate(design.blocks or []):
                ctx_lines.append(f"Block {i+1}: {b.get('time')} {b.get('title')} — {b.get('type')}")

        ctx = "\n".join(ctx_lines)

        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500

        if question:
            user_msg = (
                f"Facilitator question (answer in {lang_name}, plain text, short paragraphs or bullets, no preamble):\n"
                f"{question}\n\n---\n{ctx}"
            )
        else:
            user_msg = (
                f"Give a concise facilitator cheat sheet in {lang_name}: opening phrases, 1–2 watch-outs, "
                f"one tip if discussion stalls. Max 120 words. Plain text, bullets allowed. No greeting.\n\n{ctx}"
            )

        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior meeting facilitator. Reply only with helpful text, no JSON.",
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.6,
            max_tokens=600,
        )
        answer = (response.choices[0].message.content or "").strip()
        return jsonify({"answer": answer}), 200
    except Exception as e:
        print(f"ai_facilitator_help: {e}")
        return jsonify({"error": "Не удалось получить ответ"}), 500


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
        locale = (data.get("locale") or "ru").strip()[:12]

        if not all([meeting_type, goal, duration]):
            return jsonify({"error": "Отсутствуют обязательные поля"}), 400
        
        prompt = generate_meeting_prompt(meeting_type, goal, duration, constraints, locale=locale)
        
        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500
        
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по фасилитации встреч. Отвечай только в формате JSON без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            response_format=MEETING_SCHEMA,
        )

        blocks_obj = json.loads(response.choices[0].message.content)
        blocks = blocks_obj["blocks"]
        
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
        locale = (data.get("locale") or "ru").strip()[:12]

        prompt = regenerate_block_prompt(current_block, meeting_context, locale=locale)
        
        client = get_openai_client()
        if not client:
            return jsonify({"error": "OpenAI API не настроен"}), 500
        
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
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

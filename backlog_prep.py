from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI

from database import db
from models import BacklogWorkItem

bp_backlog_prep = Blueprint("backlog_prep", __name__, url_prefix="/api/backlog")

MAX_SPEC_CHARS = 100_000
MAX_UPLOAD_BYTES = 600_000

BACKLOG_ASSIST_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "backlog_prep_assist",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "suggested_text": {"type": "string"},
                "suggested_context": {"type": "string"},
                "suggested_acceptance_criteria": {"type": "string"},
                "suggested_nfr": {"type": "string"},
            },
            "required": [
                "suggested_text",
                "suggested_context",
                "suggested_acceptance_criteria",
                "suggested_nfr",
            ],
            "additionalProperties": False,
        },
    },
}

SPEC_DECOMPOSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "spec_decompose",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "epic_title": {"type": "string", "minLength": 1, "maxLength": 220},
                "epic_description": {"type": "string", "minLength": 1},
                "epic_context": {"type": "string"},
                "suggested_stories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "minLength": 1, "maxLength": 220},
                            "summary": {"type": "string", "minLength": 1},
                            "acceptance_hint": {"type": "string"},
                        },
                        "required": ["title", "summary", "acceptance_hint"],
                        "additionalProperties": False,
                    },
                    "minItems": 2,
                    "maxItems": 15,
                },
            },
            "required": ["epic_title", "epic_description", "epic_context", "suggested_stories"],
            "additionalProperties": False,
        },
    },
}


def _get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _current_user_id() -> int:
    return int(get_jwt_identity())


def _build_prompt(
    text: str,
    work_type: str,
    context: Optional[str],
    language: str,
    acceptance_criteria: Optional[str],
    nfr: Optional[str],
) -> List[dict]:
    system = (
        "Ты опытный Agile-коуч и бизнес-аналитик. Помогай уточнять user story или epic "
        "по канонам INVEST, проверяй и дополняй критерии приёмки и нефункциональные требования, "
        "и обязательно возвращай JSON с ключами missing_fields, questions, "
        "suggestions, improved_example. Используй тот же язык ответа, что указал пользователь."
    )
    user = (
        f"Тип: {work_type}\n"
        f"Язык ответа: {language}\n"
        f"Описание:\n{text}\n"
        f"Контекст/цель:\n{context or 'не указано'}\n"
        f"Критерии приёмки (если есть):\n{acceptance_criteria or 'не указано'}\n"
        f"Нефункциональные требования (если есть):\n{nfr or 'не указано'}\n"
        "Верни только JSON без markdown."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _normalize_spec_text(raw: str) -> str:
    text = (raw or "").strip()
    if len(text) > MAX_SPEC_CHARS:
        text = text[:MAX_SPEC_CHARS] + "\n\n[… текст обрезан для анализа …]"
    return text


def _read_uploaded_text(file_storage) -> tuple[Optional[str], Optional[str]]:
    if not file_storage or not file_storage.filename:
        return None, None
    name = (file_storage.filename or "").lower()
    if not name.endswith((".txt", ".md", ".markdown", ".csv")):
        return None, "Поддерживаются файлы .txt, .md, .markdown, .csv (или вставьте текст в поле)"
    data = file_storage.read()
    if len(data) > MAX_UPLOAD_BYTES:
        return None, f"Файл слишком большой (макс. {MAX_UPLOAD_BYTES // 1000} KB)"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    return text, None


@bp_backlog_prep.route("/prep", methods=["POST"])
@jwt_required()
def prepare_backlog_item():
    data = request.get_json() or {}
    description = data.get("text", "").strip()
    work_type = data.get("work_type", "story").strip() or "story"
    context = (data.get("context") or "").strip() or None
    language = (data.get("language") or "ru").strip() or "ru"
    acceptance_criteria = (data.get("acceptance_criteria") or "").strip() or None
    nfr = (data.get("nfr") or "").strip() or None

    if not description:
        return jsonify({"error": "Описание (text) обязательно"}), 400

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OPENAI_API_KEY не задан"}), 500

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_prompt(description, work_type, context, language, acceptance_criteria, nfr),
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = completion.choices[0].message.content
        payload = json.loads(content)
        result = {
            "missing_fields": payload.get("missing_fields", []),
            "questions": payload.get("questions") or payload.get("clarifying_questions", []),
            "suggestions": payload.get("suggestions", []),
            "improved_example": payload.get("improved_example", ""),
        }
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "AI_generation_failed", "details": str(exc)}), 500


@bp_backlog_prep.route("/prep/assist", methods=["POST"])
@jwt_required()
def prep_form_assist():
    data = request.get_json() or {}
    hint = (data.get("hint") or "").strip()
    work_type = (data.get("work_type") or "story").strip() or "story"
    language = (data.get("language") or "ru").strip() or "ru"
    existing_text = (data.get("existing_text") or "").strip()
    existing_context = (data.get("existing_context") or "").strip()
    existing_ac = (data.get("existing_acceptance_criteria") or "").strip()
    existing_nfr = (data.get("existing_nfr") or "").strip()

    if not hint and not existing_text:
        return jsonify({"error": "Укажите заметку (hint) или частичное описание"}), 400

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OPENAI_API_KEY не задан"}), 500

    lang_line = "Russian" if language.startswith("ru") else "English"
    system = (
        f"You help product owners draft backlog items. Output language: {lang_line}. "
        "Return only JSON: suggested_text (user story or epic body in INVEST spirit), "
        "suggested_context (team, goal, risks, dependencies — short), "
        "suggested_acceptance_criteria (bullet lines, use - prefix per line or numbered), "
        "suggested_nfr (performance, security, availability, compliance — bullet lines or empty string). "
        "Merge and improve existing_* fields when provided."
    )
    user = (
        f"work_type: {work_type}\n"
        f"user_hint: {hint or '(none)'}\n"
        f"existing_description:\n{existing_text or '(empty)'}\n"
        f"existing_context:\n{existing_context or '(empty)'}\n"
        f"existing_acceptance_criteria:\n{existing_ac or '(empty)'}\n"
        f"existing_nfr:\n{existing_nfr or '(empty)'}\n"
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format=BACKLOG_ASSIST_SCHEMA,
            temperature=0.45,
        )
        payload = json.loads(completion.choices[0].message.content)
        return jsonify(
            {
                "suggested_text": (payload.get("suggested_text") or "").strip(),
                "suggested_context": (payload.get("suggested_context") or "").strip(),
                "suggested_acceptance_criteria": (payload.get("suggested_acceptance_criteria") or "").strip(),
                "suggested_nfr": (payload.get("suggested_nfr") or "").strip(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "AI_generation_failed", "details": str(exc)}), 500


@bp_backlog_prep.route("/spec-decompose", methods=["POST"])
@jwt_required()
def spec_decompose():
    """Разбор бизнес-спецификации: черновик эпика и варианты декомпозиции на истории."""
    spec_text = ""

    if request.content_type and "multipart/form-data" in request.content_type:
        if "file" in request.files:
            raw, ferr = _read_uploaded_text(request.files["file"])
            if ferr:
                return jsonify({"error": ferr}), 400
            spec_text = raw or ""
        pasted = (request.form.get("text") or "").strip()
        if pasted:
            spec_text = pasted if not spec_text else spec_text + "\n\n" + pasted
    else:
        body = request.get_json(silent=True) or {}
        spec_text = (body.get("text") or "").strip()

    spec_text = _normalize_spec_text(spec_text)
    if len(spec_text) < 80:
        return jsonify({"error": "Добавьте текст спецификации (от 80 символов) или загрузите .txt/.md"}), 400

    language = "ru"
    if request.content_type and "multipart/form-data" in request.content_type:
        language = (request.form.get("language") or "ru").strip() or "ru"
    else:
        language = (request.get_json(silent=True) or {}).get("language") or "ru"
        language = str(language).strip() or "ru"

    lang_name = "Russian" if str(language).startswith("ru") else "English"

    client = _get_openai_client()
    if not client:
        return jsonify({"error": "OPENAI_API_KEY не задан"}), 500

    prompt = f"""
You are a senior product owner. The following is a business specification (may be partial).

Tasks:
1) Propose ONE epic title and a clear epic description (value for users/stakeholders).
2) epic_context: stakeholders, constraints, dependencies, risks (concise).
3) suggested_stories: 2–15 user stories that decompose the epic. Each story: title (short), summary (As a / I want / so that or equivalent), acceptance_hint (initial AC bullets as plain text).

Language for all human-readable fields: {lang_name}.

Specification:
---
{spec_text}
---
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You output only JSON matching the schema. Be practical and specific.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=SPEC_DECOMPOSE_SCHEMA,
            temperature=0.35,
        )
        out = json.loads(response.choices[0].message.content)
        return jsonify(
            {
                "epic_title": out.get("epic_title", "").strip(),
                "epic_description": out.get("epic_description", "").strip(),
                "epic_context": (out.get("epic_context") or "").strip(),
                "suggested_stories": out.get("suggested_stories") or [],
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "AI_generation_failed", "details": str(exc)}), 500


def _parse_json_body() -> dict[str, Any]:
    return request.get_json(silent=True) or {}


@bp_backlog_prep.route("/items", methods=["GET"])
@jwt_required()
def list_backlog_items():
    uid = _current_user_id()
    items = (
        BacklogWorkItem.query.filter_by(user_id=uid)
        .order_by(BacklogWorkItem.updated_at.desc())
        .all()
    )
    roots = [i for i in items if i.parent_id is None]
    return jsonify({"items": [r.to_dict(include_children=True) for r in roots]})


@bp_backlog_prep.route("/items", methods=["POST"])
@jwt_required()
def create_backlog_item():
    uid = _current_user_id()
    data = _parse_json_body()
    item_type = (data.get("item_type") or "story").strip().lower()
    if item_type not in ("epic", "story"):
        return jsonify({"error": "item_type must be epic or story"}), 400

    parent_id = data.get("parent_id")
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid parent_id"}), 400
        parent = BacklogWorkItem.query.filter_by(id=parent_id, user_id=uid).first()
        if not parent:
            return jsonify({"error": "Parent not found"}), 404
        if parent.item_type != "epic":
            return jsonify({"error": "Parent must be an epic"}), 400
    else:
        parent_id = None

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    item = BacklogWorkItem(
        user_id=uid,
        parent_id=parent_id,
        item_type=item_type,
        title=title,
        description=(data.get("description") or "").strip(),
        acceptance_criteria=(data.get("acceptance_criteria") or "").strip() or None,
        nfr=(data.get("nfr") or "").strip() or None,
        context=(data.get("context") or "").strip() or None,
        decomposition_suggestions=data.get("decomposition_suggestions"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@bp_backlog_prep.route("/items/<int:item_id>", methods=["GET"])
@jwt_required()
def get_backlog_item(item_id: int):
    uid = _current_user_id()
    item = BacklogWorkItem.query.filter_by(id=item_id, user_id=uid).first()
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"item": item.to_dict(include_children=True)})


@bp_backlog_prep.route("/items/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_backlog_item(item_id: int):
    uid = _current_user_id()
    item = BacklogWorkItem.query.filter_by(id=item_id, user_id=uid).first()
    if not item:
        return jsonify({"error": "Not found"}), 404

    data = _parse_json_body()
    if "title" in data:
        t = (data.get("title") or "").strip()
        if not t:
            return jsonify({"error": "title cannot be empty"}), 400
        item.title = t
    if "description" in data:
        item.description = (data.get("description") or "").strip()
    if "acceptance_criteria" in data:
        v = data.get("acceptance_criteria")
        item.acceptance_criteria = (v or "").strip() or None
    if "nfr" in data:
        v = data.get("nfr")
        item.nfr = (v or "").strip() or None
    if "context" in data:
        v = data.get("context")
        item.context = (v or "").strip() or None
    if "decomposition_suggestions" in data:
        item.decomposition_suggestions = data.get("decomposition_suggestions")

    if "parent_id" in data:
        new_parent = data.get("parent_id")
        if new_parent is None:
            item.parent_id = None
        else:
            try:
                pid = int(new_parent)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid parent_id"}), 400
            if pid == item.id:
                return jsonify({"error": "Cannot set parent to self"}), 400
            parent = BacklogWorkItem.query.filter_by(id=pid, user_id=uid).first()
            if not parent or parent.item_type != "epic":
                return jsonify({"error": "Invalid parent epic"}), 400
            item.parent_id = pid

    if "item_type" in data:
        nt = (data.get("item_type") or "").strip().lower()
        if nt not in ("epic", "story"):
            return jsonify({"error": "Invalid item_type"}), 400
        if nt == "story" and item.children:
            return jsonify({"error": "Convert children first — epic has stories"}), 400
        item.item_type = nt

    db.session.commit()
    return jsonify({"item": item.to_dict(include_children=True)})


@bp_backlog_prep.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_backlog_item(item_id: int):
    uid = _current_user_id()
    item = BacklogWorkItem.query.filter_by(id=item_id, user_id=uid).first()
    if not item:
        return jsonify({"error": "Not found"}), 404
    if item.item_type == "epic":
        for ch in list(item.children):
            db.session.delete(ch)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})


@bp_backlog_prep.route("/items/from-spec", methods=["POST"])
@jwt_required()
def create_epic_bundle_from_spec():
    """Сохранить эпик + дочерние истории из ответа spec-decompose (без повторного ИИ)."""
    uid = _current_user_id()
    data = _parse_json_body()
    epic_title = (data.get("epic_title") or "").strip()
    epic_description = (data.get("epic_description") or "").strip()
    epic_context = (data.get("epic_context") or "").strip()
    stories = data.get("suggested_stories") or []
    if not epic_title or not epic_description:
        return jsonify({"error": "epic_title and epic_description required"}), 400
    if not isinstance(stories, list):
        return jsonify({"error": "suggested_stories must be a list"}), 400

    epic = BacklogWorkItem(
        user_id=uid,
        parent_id=None,
        item_type="epic",
        title=epic_title,
        description=epic_description,
        context=epic_context or None,
        decomposition_suggestions=stories,
    )
    db.session.add(epic)
    db.session.flush()

    created_stories: List[dict] = []
    for row in stories:
        if not isinstance(row, dict):
            continue
        st_title = (row.get("title") or "").strip()
        summary = (row.get("summary") or "").strip()
        ac_hint = (row.get("acceptance_hint") or "").strip()
        if not st_title or not summary:
            continue
        desc = summary
        ac = ac_hint or None
        child = BacklogWorkItem(
            user_id=uid,
            parent_id=epic.id,
            item_type="story",
            title=st_title,
            description=desc,
            acceptance_criteria=ac,
            context=None,
        )
        db.session.add(child)
        created_stories.append(
            {
                "title": st_title,
                "description": desc,
                "acceptance_criteria": ac or "",
            }
        )

    db.session.commit()
    epic_full = BacklogWorkItem.query.filter_by(id=epic.id, user_id=uid).first()
    return jsonify({"item": epic_full.to_dict(include_children=True)}), 201


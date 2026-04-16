# Инструмент быстрой оценки бизнес-ценности историй / эпиков / фич.
from __future__ import annotations

import base64
import json
import os
import uuid
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request
from openai import OpenAI

from ai_limits import check_and_consume_ai_quota

bp_business_value = Blueprint("business_value", __name__, url_prefix="/api/business-value")

MAX_PARSE_TEXT = 24_000
MAX_IMAGE_BYTES = 4 * 1024 * 1024

# polarity +1 — суммируется, -1 — вычитается (как «Риск» в методичке).
FACTOR_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "profit",
        "polarity": 1,
        "label_ru": "Прибыль / бизнес-ценность",
        "label_en": "Profit / business value",
        "hint5_ru": "Прямой рост выручки или NPS",
        "hint1_ru": "Нет измеримого эффекта",
        "hint5_en": "Direct revenue or NPS impact",
        "hint1_en": "No measurable effect",
    },
    {
        "id": "urgency",
        "polarity": 1,
        "label_ru": "Срочность",
        "label_en": "Urgency",
        "hint5_ru": "Жёсткий дедлайн регулятора / рынка",
        "hint1_ru": "Можно отложить на квартал",
        "hint5_en": "Hard regulator or market deadline",
        "hint1_en": "Can slip a quarter",
    },
    {
        "id": "regulatory",
        "polarity": 1,
        "label_ru": "Регуляторный риск (если не сделать)",
        "label_en": "Regulatory exposure",
        "hint5_ru": "Штраф или запрет операций",
        "hint1_ru": "Нет регуляторных последствий",
        "hint5_en": "Fine or ban on operations",
        "hint1_en": "No regulatory consequences",
    },
    {
        "id": "delivery_risk",
        "polarity": -1,
        "label_ru": "Риск невыполнения",
        "label_en": "Delivery / fulfillment risk",
        "hint5_ru": "Много зависимостей, высокая неопределённость",
        "hint1_ru": "Всё под контролем команды",
        "hint5_en": "Many dependencies, high uncertainty",
        "hint1_en": "Fully under team control",
    },
    {
        "id": "customer_impact",
        "polarity": 1,
        "label_ru": "Влияние на клиента",
        "label_en": "Customer impact",
        "hint5_ru": "Сильно улучшает CX / убирает боль",
        "hint1_ru": "Почти не заметят",
        "hint5_en": "Strong CX improvement",
        "hint1_en": "Barely noticeable",
    },
    {
        "id": "strategic_fit",
        "polarity": 1,
        "label_ru": "Стратегическое соответствие",
        "label_en": "Strategic fit",
        "hint5_ru": "Явно в стратегии продукта / банка",
        "hint1_ru": "Вне фокуса",
        "hint5_en": "Clearly on-strategy",
        "hint1_en": "Off focus",
    },
]


def _openai_client() -> OpenAI | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    return OpenAI(api_key=key, timeout=timeout)


def _normalize_items(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for el in raw[:40]:
        if not isinstance(el, dict):
            continue
        title = str(el.get("title") or "").strip()
        if not title or len(title) > 500:
            continue
        desc = str(el.get("description") or el.get("summary") or "").strip()[:2000]
        it = str(el.get("item_type") or el.get("type") or "story").strip().lower()
        if it not in ("story", "epic", "feature", "unknown"):
            it = "story"
        out.append(
            {
                "id": str(el.get("id") or uuid.uuid4()),
                "title": title,
                "description": desc,
                "item_type": it if it != "unknown" else "story",
            }
        )
    return out


@bp_business_value.route("/factors", methods=["GET"])
def list_factors():
    """Пул факторов для выбора на фронте."""
    return jsonify({"factors": FACTOR_CATALOG})


def _parse_with_openai_text(text: str, lang: str) -> List[Dict[str, Any]]:
    client = _openai_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY не задан")
    lang = "en" if lang == "en" else "ru"
    prompt = (
        "Извлеки из текста список элементов бэклога: пользовательские истории, эпики, фичи, задачи. "
        "Для каждого: короткий title и при наличии description.\n"
        "Ответ строго JSON: {\"items\":[{\"title\":\"...\",\"description\":\"...\",\"item_type\":\"story|epic|feature\"}]}\n"
        f"Язык исходного текста: {lang}. Не добавляй пояснений вне JSON."
        if lang == "ru"
        else "Extract backlog items (stories, epics, features). JSON only: "
        '{"items":[{"title":"...","description":"...","item_type":"story|epic|feature"}]}'
    )
    resp = client.chat.completions.create(
        model=os.getenv("BUSINESS_VALUE_PARSE_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": "You output only valid minified JSON."},
            {"role": "user", "content": f"{prompt}\n\n---\n{text[:MAX_PARSE_TEXT]}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return _normalize_items(data.get("items"))


def _parse_with_openai_image(image_bytes: bytes, mime: str, lang: str) -> List[Dict[str, Any]]:
    client = _openai_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY не задан")
    b64 = base64.b64encode(image_bytes).decode("ascii")
    mime = mime if mime in ("image/png", "image/jpeg", "image/webp", "image/gif") else "image/png"
    lang = "en" if lang == "en" else "ru"
    user_txt = (
        "На скриншоте — бэклог, Jira, Excel или доска. Извлеки все истории/эпики/фичи: title и при наличии описание. "
        "Ответ JSON: {\"items\":[{\"title\":\"...\",\"description\":\"...\",\"item_type\":\"story|epic|feature\"}]}"
        if lang == "ru"
        else "Screenshot of backlog/Jira/board. Extract items as JSON "
        '{"items":[{"title":"...","description":"...","item_type":"story|epic|feature"}]}'
    )
    resp = client.chat.completions.create(
        model=os.getenv("BUSINESS_VALUE_VISION_MODEL", "gpt-4.1"),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_txt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return _normalize_items(data.get("items"))


@bp_business_value.route("/parse-items", methods=["POST"])
def parse_items():
    """Текст или изображение → список элементов для оценки (списывает AI-квоту)."""
    lang = (request.args.get("lang") or request.form.get("lang") or "ru").lower()
    lang = "en" if lang == "en" else "ru"

    if request.content_type and "multipart/form-data" in request.content_type:
        if "image" not in request.files and "screenshot" not in request.files:
            return jsonify({"error": "Нужен файл image или screenshot"}), 400
        f = request.files.get("image") or request.files.get("screenshot")
        if not f or not f.filename:
            return jsonify({"error": "Пустой файл"}), 400
        raw = f.read()
        if len(raw) > MAX_IMAGE_BYTES:
            return jsonify({"error": "Файл слишком большой (макс. 4 МБ)"}), 400
        mime = f.mimetype or "image/png"
        check_and_consume_ai_quota()
        try:
            items = _parse_with_openai_image(raw, mime, lang)
        except Exception as e:
            return jsonify({"error": str(e)[:500]}), 502
        return jsonify({"items": items})

    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Передайте JSON { \"text\": \"...\" } или multipart с image"}), 400
    if len(text) > MAX_PARSE_TEXT:
        return jsonify({"error": "Текст слишком длинный"}), 400
    check_and_consume_ai_quota()
    try:
        items = _parse_with_openai_text(text, lang)
    except Exception as e:
        return jsonify({"error": str(e)[:500]}), 502
    return jsonify({"items": items})


@bp_business_value.route("/score-preview", methods=["POST"])
def score_preview():
    """Серверная проверка формулы (опционально); основная логика на фронте."""
    data = request.get_json(silent=True) or {}
    scores = data.get("scores")
    factor_ids = data.get("factor_ids")
    if not isinstance(scores, dict) or not isinstance(factor_ids, list):
        return jsonify({"error": "Нужны scores {id:1..5} и factor_ids []"}), 400
    by_id = {f["id"]: f for f in FACTOR_CATALOG}
    total = 0
    for fid in factor_ids:
        if fid not in by_id:
            continue
        v = scores.get(fid)
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if n < 1 or n > 5:
            continue
        total += n * by_id[fid]["polarity"]
    band = "defer"
    if total >= 12:
        band = "immediate"
    elif total >= 7:
        band = "quarter"
    return jsonify({"score": total, "band": band})

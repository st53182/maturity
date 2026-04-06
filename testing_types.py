# Задание 3: Типы тестирования для Growboard (Опрос + Дашборд)
# API для оценки определений студентов нейросетью (1-5) и выдачи эталона после 5 попыток

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os

bp_testing_types = Blueprint("testing_types", __name__, url_prefix="/api/testing-types")

# Эталонные определения типов тестирования (контекст: приложение Growboard, разделы Опрос и Дашборд)
REFERENCE = {
    "performance": {
        "name_ru": "Performance Testing",
        "name_en": "Performance Testing",
        "definition_ru": "Измеряет время отклика системы при выполнении запросов одним или несколькими пользователями. Определяет, насколько быстро работает приложение под нагрузкой. Для Growboard: как быстро открываются опросы и дашборд, отрисовываются графики.",
    },
    "load": {
        "name_ru": "Load Testing",
        "name_en": "Load Testing",
        "definition_ru": "Проверяет поведение системы при определённой нагрузке, когда многие пользователи работают одновременно, как в реальной жизни. Для Growboard: одновременное прохождение опросов, открытие дашборда многими пользователями.",
    },
    "stress": {
        "name_ru": "Stress Testing",
        "name_en": "Stress Testing",
        "definition_ru": "Проверяет верхние пределы допустимой нагрузки при экстремальных условиях. Что происходит, когда система «ломается»? Как она восстанавливается? Для Growboard: при какой нагрузке падают опросы или дашборд.",
    },
    "security": {
        "name_ru": "Security Testing",
        "name_en": "Security Testing",
        "definition_ru": "Определяет угрозы, измеряет уязвимости и помогает обнаружить все возможные риски безопасности. Включает тестирование на prompt injection в AI-системах. Для Growboard: доступ к чужим опросам, защита данных дашборда.",
    },
    "usability": {
        "name_ru": "Usability Testing",
        "name_en": "Usability Testing",
        "definition_ru": "Проводится с точки зрения конечного пользователя: легко ли приложением пользоваться? Интуитивно ли оно? Удобно ли? Для Growboard: насколько понятно создание опроса, чтение дашборда.",
    },
    "accessibility": {
        "name_ru": "Accessibility Testing",
        "name_en": "Accessibility Testing",
        "definition_ru": "Подмножество usability: доступно ли приложение для людей с ограниченными возможностями (слух, дальтонизм, пожилой возраст)? Для Growboard: контраст, шрифты, навигация с клавиатуры в опросах и дашборде.",
    },
    "failover": {
        "name_ru": "Failover and Recovery Testing",
        "name_en": "Failover and Recovery Testing",
        "definition_ru": "Определяет, можно ли продолжить операции после аварии или потери целостности системы. Насколько быстро система восстанавливается? Для Growboard: восстановление после сбоя при прохождении опроса или загрузке дашборда.",
    },
    "smoke": {
        "name_ru": "Smoke Testing",
        "name_en": "Smoke Testing",
        "definition_ru": "Проверка исправности критических частей системы. «Дымовой тест» — быстрая проверка: не «горит» ли система? Запускается после каждого нового билда перед более детальным тестированием. Для Growboard: открывается ли опрос и дашборд после деплоя.",
    },
    "sanity": {
        "name_ru": "Sanity Testing",
        "name_en": "Sanity Testing",
        "definition_ru": "Проверка основных функций приложения без глубокого погружения. Убедиться, что конкретная функциональность работает после небольших изменений. Узкофокусный подход. Для Growboard: после правки бага в опросе — базовая проверка опроса и дашборда.",
    },
    "regression": {
        "name_ru": "Regression Testing",
        "name_en": "Regression Testing",
        "definition_ru": "Гарантирует, что старый код по-прежнему работает после внесения новых изменений. Один из самых важных типов в CI/CD — полностью автоматизируется в современных пайплайнах. Для Growboard: регрессия в опросах и дашборде после релиза.",
    },
    "e2e": {
        "name_ru": "End-to-End (E2E) Testing",
        "name_en": "End-to-End (E2E) Testing",
        "definition_ru": "Комплексное тестирование реального пользовательского сценария от начала до конца, включая интеграцию с внешними системами. Имитирует полный путь пользователя. Для Growboard: сценарий от входа до прохождения опроса и просмотра результатов на дашборде.",
    },
    "adhoc": {
        "name_ru": "Ad-hoc Testing",
        "name_en": "Ad-hoc Testing",
        "definition_ru": "Неформальный, неструктурированный тип тестирования с целью сломать систему. Никаких заранее запланированных тест-кейсов. Требует интуиции и опыта тестировщика. Для Growboard: свободное «ломание» опросов и дашборда.",
    },
    "exploratory": {
        "name_ru": "Exploratory Testing",
        "name_en": "Exploratory Testing",
        "definition_ru": "Всё об открытиях, исследованиях и обучении. Тест-кейсы не планируются заранее, документации нет. Тестировщик изучает систему и тестирует одновременно — мощный инструмент опытного QA. Для Growboard: исследование опросов и дашборда без чек-листа.",
    },
}


def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@bp_testing_types.route("/list", methods=["GET"])
def list_types():
    """Список типов тестирования для задания."""
    lang = request.args.get("lang", "ru")
    items = []
    for key, data in REFERENCE.items():
        items.append({
            "key": key,
            "name": data["name_ru"] if lang == "ru" else data["name_en"],
        })
    return jsonify({"items": items})


@bp_testing_types.route("/evaluate", methods=["POST"])
@jwt_required()
def evaluate():
    """
    Оценка определения студента по шкале 1-5.
    Body: { "type_key": "smoke", "user_definition": "..." }
    Returns: { "score": 1-5, "feedback": "..." }
    """
    data = request.json or {}
    type_key = (data.get("type_key") or "").strip()
    user_definition = (data.get("user_definition") or "").strip()

    if not type_key or type_key not in REFERENCE:
        return jsonify({"error": "Неверный type_key"}), 400
    if not user_definition:
        return jsonify({"error": "Введите определение"}), 400

    ref = REFERENCE[type_key]
    ref_text = ref["definition_ru"]
    name = ref["name_ru"]

    client = get_openai_client()
    prompt = f"""Ты эксперт по тестированию ПО. Контекст: приложение — Growboard (разделы «Опрос» и «Дашборд»).

Тип тестирования: {name}
Эталон (как правильно понимать этот тип): {ref_text}

Студент описал по шагам, как он видит процесс этого тестирования для Growboard:
{user_definition}

Оцени по шкале 1–5, насколько шаги студента соответствуют эталону и применимы к Опросу и Дашборду:
5 — процесс описан верно и по шагам, применимо к Growboard
4 — в целом верно, небольшие неточности
3 — частично верно, упущена существенная часть
2 — в основном неверно или не по теме
1 — неверно или не про этот тип тестирования

Ответь СТРОГО в формате JSON, без другого текста:
{{"score": <число 1-5>, "feedback": "<короткий комментарий на русском 1-2 предложения>"}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Ты оцениваешь ответы студентов. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        content = (response.choices[0].message.content or "").strip()
        import json as json_lib
        try:
            out = json_lib.loads(content)
        except json_lib.JSONDecodeError:
            start = content.find("{")
            if start >= 0:
                depth = 0
                end = start
                for i, c in enumerate(content[start:], start):
                    if c == "{": depth += 1
                    elif c == "}": depth -= 1
                    if depth == 0:
                        end = i
                        break
                try:
                    out = json_lib.loads(content[start:end + 1])
                except json_lib.JSONDecodeError:
                    out = {}
            else:
                out = {}
        score = out.get("score")
        if isinstance(score, (int, float)):
            score = max(1, min(5, int(score)))
        else:
            score = 3
        return jsonify({
            "score": score,
            "feedback": out.get("feedback", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_testing_types.route("/suggest/<type_key>", methods=["GET"])
@jwt_required()
def suggest(type_key):
    """После 5 неудачных попыток — выдать эталонное определение."""
    if type_key not in REFERENCE:
        return jsonify({"error": "Неверный type_key"}), 404
    return jsonify({
        "suggestion": REFERENCE[type_key]["definition_ru"],
        "name": REFERENCE[type_key]["name_ru"],
    })


@bp_testing_types.route("/example-report", methods=["POST"])
@jwt_required()
def example_report():
    """
    При оценке 5 баллов — сгенерировать краткий пример отчёта по тестированию.
    Body: { "type_key": "smoke", "user_steps": "..." }
    Returns: { "report": "..." }
    """
    data = request.json or {}
    type_key = (data.get("type_key") or "").strip()
    user_steps = (data.get("user_steps") or data.get("user_definition") or "").strip()

    if not type_key or type_key not in REFERENCE:
        return jsonify({"error": "Неверный type_key"}), 400

    name = REFERENCE[type_key]["name_ru"]
    client = get_openai_client()

    prompt = f"""Контекст: приложение Growboard (разделы «Опрос» и «Дашборд»). Тип тестирования: {name}.

Студент описал шаги тестирования:
{user_steps or "(не указано)"}

Сгенерируй КРАТКИЙ пример отчёта о тестировании в виде структурированного текста с переносами строк, как в реальном отчёте.

Формат (обязательно придерживайся именно такого порядка и заголовков, без лишних пометок):
Объект тестирования: ...
Цель: ...
Шаги: 
- ...
- ...
Результаты: ...
Выводы и рекомендации: ...

Требования:
- максимум 8–10 строк;
- без Markdown, без нумерованных заголовков вида \"1.\", только обычный текст и дефисы для шагов;
- пиши по-русски;
- никаких пояснений вне самого отчёта (никаких «Вот отчёт:» и т.п.)."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Ты пишешь краткие структурированные отчёты о тестировании ПО. Соблюдай запрошенный формат и не добавляй ничего лишнего."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=400,
        )
        report = (response.choices[0].message.content or "").strip()
        return jsonify({"report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

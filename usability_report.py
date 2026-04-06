# Задание 4: Usability Test Report — помощь нейросети по разделам отчёта

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

bp_usability_report = Blueprint("usability_report", __name__, url_prefix="/api/usability-report")

SECTION_PROMPTS = {
    "metadata": "Раздел 1 — Метаданные отчёта (Report ID, проект, продукт, версия, среда, дата, исследователь). Подскажи, как кратко и единообразно заполнять эти поля для usability-теста.",
    "objectives": "Раздел 2 — Цели тестирования (Primary/Secondary objectives, Success criteria). Объясни, как формулировать измеримые цели и критерии успеха для юзабилити-теста.",
    "participants": "Раздел 3 — Участники тестирования (количество, профиль, таблица Participant ID / Role / Experience / Notes). Дай рекомендации по подбору и описанию участников.",
    "scenarios": "Раздел 4 — Сценарии тестирования (Scenario ID, описание, предусловия, шаги задачи, ожидаемый результат). Как правильно описать сценарий и шаги для пользователя?",
    "performance": "Раздел 5 — Результаты выполнения задач (таблица по участникам: выполнено да/нет, время, ошибки, помощь, заметки; среднее время, успешность, наблюдения). Как интерпретировать и кратко описать?",
    "issues": "Раздел 6 — Юзабилити-проблемы (Issue ID, описание, сценарий, шаги воспроизведения, наблюдаемое/ожидаемое поведение, влияние, частота, severity 1–5, рекомендация). Как формулировать и ранжировать проблемы?",
    "feedback": "Раздел 7 — Обратная связь пользователей (цитаты, боли, положительные наблюдения). Как структурировать и цитировать?",
    "metrics": "Раздел 8 — Метрики юзабилити (Task Success Rate, время, Error rate, удовлетворённость, SUS). Какие метрики указывать и как их считать?",
    "summary": "Раздел 9 — Итог (риски, общая оценка UX, рекомендации команде). Как кратко и по делу сформулировать выводы?",
    "attachments": "Раздел 10 — Вложения (скриншоты, записи сессий, тепловые карты). Что обычно прикладывают к отчёту и как на это сослаться?",
}


def get_openai_client():
    import os
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


@bp_usability_report.route("/help", methods=["POST"])
@jwt_required()
def help_section():
    """
    Помощь нейросети по разделу отчёта.
    Body: { "section": "metadata" | "objectives" | ... | "attachments", "context": "опционально текст пользователя" }
    Returns: { "suggestion": "..." }
    """
    data = request.json or {}
    section = (data.get("section") or "").strip().lower()
    context = (data.get("context") or "").strip()

    if section not in SECTION_PROMPTS:
        return jsonify({"error": "Неверный раздел"}), 400

    client = get_openai_client()
    if not client:
        return jsonify({"error": "Сервис помощи недоступен"}), 503

    prompt = SECTION_PROMPTS[section]
    if context:
        prompt += f"\n\nКонтекст от пользователя (уже заполнено или черновик):\n{context}\n\nДай краткие подсказки или пример формулировок с учётом этого контекста. Ответ на русском, по делу, 3–8 предложений."
    else:
        prompt += "\n\nДай краткие подсказки или пример формулировок. Ответ на русском, 3–8 предложений."

    try:
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "Ты помощник по составлению отчётов юзабилити-тестирования. Отвечай кратко, на русском, с примерами где уместно."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=500,
        )
        text = (response.choices[0].message.content or "").strip()
        return jsonify({"suggestion": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Оценка зрелости по ссылке: создание сессии, прохождение (да/нет), результаты для радара и PDF.
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import MaturityLinkSession
from maturity_questions import MATURITY_QUESTIONS, RADAR_GROUPS, ROLE_BY_THEME

maturity_bp = Blueprint('maturity_link', __name__)

QUESTIONS_COUNT = len(MATURITY_QUESTIONS)
QUESTIONS_PER_THEME = 3

# Индексы вопросов по темам (для радара)
def _theme_indices():
    from collections import OrderedDict
    out = OrderedDict()
    for i, q in enumerate(MATURITY_QUESTIONS):
        theme = q["theme"]
        if theme not in out:
            out[theme] = []
        out[theme].append(i)
    return out

THEME_INDICES = _theme_indices()


def _results_from_answers(answers):
    """answers: list of bool. Return { theme: { "1".."3": 0-5 } } for radar."""
    if not answers or len(answers) != QUESTIONS_COUNT:
        return {}
    results = {}
    for theme, indices in THEME_INDICES.items():
        results[theme] = {}
        for sub_one_based, q_idx in enumerate(indices[:QUESTIONS_PER_THEME], 1):
            results[theme][str(sub_one_based)] = 5.0 if answers[q_idx] else 0.0
    return results


@maturity_bp.route('/api/maturity-link', methods=['POST'])
@jwt_required(optional=True)
def create_maturity_link():
    """Создать сессию оценки по ссылке. Тело: { "team_name": "опционально" }. Возвращает token и url."""
    data = request.get_json() or {}
    team_name = data.get('team_name', '').strip() or None
    token = str(uuid.uuid4())
    session = MaturityLinkSession(access_token=token, team_name=team_name)
    db.session.add(session)
    db.session.commit()
    base = request.host_url.rstrip('/')
    return jsonify({
        'token': token,
        'url': f'{base}/maturity/{token}',
        'team_name': session.team_name
    }), 201


@maturity_bp.route('/api/maturity/<token>', methods=['GET'])
def get_maturity_survey(token):
    """Публично: получить опрос по токену (вопросы с id 0..N-1, по 10 на страницу)."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена или недействительна'}), 404
    questions = [
        {
            'id': i,
            'category': q['category'],
            'theme': q['theme'],
            'text': q['text'],
            'why_important': q.get('why_important', ''),
            'metrics_impact': q.get('metrics_impact', ''),
            'negative_for_business': q.get('negative_for_business', ''),
            'related_roles': ROLE_BY_THEME.get(q['theme'], []),
        }
        for i, q in enumerate(MATURITY_QUESTIONS)
    ]
    return jsonify({
        'team_name': session.team_name,
        'completed': session.completed_at is not None,
        'questions': questions
    })


@maturity_bp.route('/api/maturity/<token>/submit', methods=['POST'])
def submit_maturity_answers(token):
    """Публично: отправить ответы. Тело: { "answers": [true, false, ... ] } — N элементов."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if session.completed_at:
        return jsonify({'error': 'Оценка уже пройдена', 'results_url': f'/maturity/{token}/results'}), 400
    data = request.get_json()
    answers = data.get('answers')
    if not isinstance(answers, list) or len(answers) != QUESTIONS_COUNT:
        return jsonify({'error': f'Нужен массив из {QUESTIONS_COUNT} ответов (да/нет)'}), 400
    # normalize to bool
    normalized = [bool(a) for a in answers]
    from datetime import datetime
    session.answers = normalized
    session.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'message': 'Ответы сохранены',
        'results_url': f'/maturity/{token}/results'
    }), 200


@maturity_bp.route('/api/maturity/<token>/results', methods=['GET'])
def get_maturity_results(token):
    """Публично: результаты для радара и PDF. Формат results как team_results (category -> subcategory -> score 0-5)."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if not session.completed_at or not session.answers:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    results = _results_from_answers(session.answers)
    completed_at = session.completed_at.isoformat() if session.completed_at else None
    return jsonify({
        'team_name': session.team_name or 'Команда',
        'completed_at': completed_at,
        'results': results,
        'radar_groups': RADAR_GROUPS,
    })


@maturity_bp.route('/api/maturity/<token>/recommendations', methods=['POST'])
def get_maturity_recommendations(token):
    """Публично: сгенерировать рекомендации по результатам через OpenAI."""
    import os
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена'}), 404
    if not session.completed_at or not session.answers:
        return jsonify({'error': 'Оценка ещё не пройдена'}), 400
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({'error': 'Сервис рекомендаций не настроен (OPENAI_API_KEY)'}), 503

    results = _results_from_answers(session.answers)
    # Сводка: по каждой категории средний балл (0–5) и доля «да»
    summary_lines = []
    for cat, subs in results.items():
        vals = [float(v) for v in subs.values()]
        avg = sum(vals) / len(vals) if vals else 0
        yes_count = sum(1 for v in vals if v >= 5)
        summary_lines.append(f"- {cat}: средний балл {avg:.1f}/5, ответов «да» {yes_count}/{len(vals)}")

    summary_text = "\n".join(summary_lines)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    prompt = f"""Ты опытный Agile-коуч. По результатам оценки зрелости команды (да/нет по темам) дай конкретные рекомендации по улучшению.

Результаты по категориям (балл 0–5, где 5 = «да»):
{summary_text}

Требования:
- Сфокусируйся на категориях с низким баллом; для сильных сторон можно дать 1–2 совета по усилению.
- Рекомендации должны быть практичными: что сделать, к кому обратиться, какие форматы ввести.
- Используй короткие параграфы и при необходимости списки. Можно использовать HTML: <p>, <ul>, <li>, <strong>.
- Ответ только на русском."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты Agile-коуч. Дай структурированные рекомендации по улучшению зрелости команды на основе данных оценки."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

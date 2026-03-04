# Оценка зрелости по ссылке: создание сессии, прохождение (да/нет), результаты для радара и PDF.
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import MaturityLinkSession
from maturity_questions import MATURITY_QUESTIONS

maturity_bp = Blueprint('maturity_link', __name__)

QUESTIONS_COUNT = len(MATURITY_QUESTIONS)


def _results_from_answers(answers):
    """answers: list of 205 bool. Return { category: { "1": 0-5, "2": 0-5, ... } } for radar."""
    if not answers or len(answers) != QUESTIONS_COUNT:
        return {}
    results = {}
    for i, q in enumerate(MATURITY_QUESTIONS):
        cat = q["category"]
        if cat not in results:
            results[cat] = {}
        # subcategory as "1".."5" within category (5 questions per category)
        sub_idx = (i % 5) + 1
        results[cat][str(sub_idx)] = 5.0 if answers[i] else 0.0
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
    """Публично: получить опрос по токену (вопросы с id 0..204)."""
    session = MaturityLinkSession.query.filter_by(access_token=token).first()
    if not session:
        return jsonify({'error': 'Ссылка не найдена или недействительна'}), 404
    questions = [
        {'id': i, 'category': q['category'], 'text': q['text']}
        for i, q in enumerate(MATURITY_QUESTIONS)
    ]
    return jsonify({
        'team_name': session.team_name,
        'completed': session.completed_at is not None,
        'questions': questions
    })


@maturity_bp.route('/api/maturity/<token>/submit', methods=['POST'])
def submit_maturity_answers(token):
    """Публично: отправить ответы. Тело: { "answers": [true, false, ... ] } — 205 элементов."""
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
        'results': results
    })
